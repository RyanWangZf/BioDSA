import shutil
import io
import os
import tarfile
import traceback
from typing import List, Tuple, Dict, Callable
import uuid
import docker
from docker.errors import NotFound
import threading
from datetime import datetime
from typing import Union
from pydantic import BaseModel
import pandas as pd
import logging
import time
import tiktoken

# executino sandbox constants
SANDBOX_IMANGE_IDENTIFIER = "biodsa-sandbox-py:latest" # this docker image must be built in advance
DEFAULT_REMOTE_PATH = "/workdir"

def truncate_middle_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text by removing tokens from the middle while preserving the beginning and end.
    """
    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        # Account for the truncation marker's tokens
        truncation_marker = "\n[... truncated ...]\n"
        marker_tokens = len(encoding.encode(truncation_marker))
        
        # Subtract marker tokens from budget
        available_tokens = max_tokens - marker_tokens
        if available_tokens < 2:
            # If we don't have enough tokens, just return the truncation marker
            return truncation_marker
        
        # Split remaining budget between start and end
        tokens_from_start = available_tokens // 2
        tokens_from_end = available_tokens - tokens_from_start
        
        return encoding.decode(tokens[:tokens_from_start]) + truncation_marker + encoding.decode(tokens[-tokens_from_end:])
    return text

class Artifact(BaseModel):
    """
    Define the output artifact of code generation and execution
    """
    content: Union[bytes,str] = None # content of the artifact in bytes (like img) or string (like txt, html)
    file_name: str = None # the name of the artifact
    file_path: str = None # the path of the artifact in the local file system
    file_type: str = None # type of the artifact, e.g., "image", "csv", "json", "html", "pdf"

    def __str__(self) -> str:
        return f"""Artifact <{self.file_name}>"""

class UploadDataset:
    
    tables: Dict[str, pd.DataFrame] = {}
    
    def __init__(
        self, 
        local_table_paths: List[str], 
        target_table_paths: List[str],
    ):
        """
        This class is used to create a dataset for the execution sandbox & agents.
        The local tables are loaded into memory as pd data frames, so they can be written into the sandbox at the target locations.
        
        Args:
            local_table_paths: the paths to the tables on the local machine
            target_table_paths: the paths to the target tables in the sandbox
            
        Note: paths should have the revelant extension for the file type, e.g. ".csv", ".txt", ".tsv"
        """
        
        assert len(local_table_paths) == len(target_table_paths), "local_table_paths and target_table_paths must have the same length"
        
        self.local_table_paths = local_table_paths
        self.target_table_paths = target_table_paths

        
    def __len__(self):
        return len(self.local_tables)
    
    def __getitem__(self, index: int):
        return self.local_tables[index], self.target_table_paths[index]
    
    def __iter__(self):
        return iter(zip(self.local_table_paths, self.target_table_paths))
    
    def __str__(self):
        return f"UploadDataset with {len(self)} tables"
    
    def __repr__(self):
        return self.__str__()


class ExecutionSandboxWrapper:
    container_id: str = None
    container: docker.models.containers.Container = None
    image: docker.models.images.Image = None
    available_files: List[str] = []
    all_artifact_files: List[str] = []
    workdir: str = DEFAULT_REMOTE_PATH

    def __init__(self, 
        image_identifier: str=SANDBOX_IMANGE_IDENTIFIER, 
        workdir: str=DEFAULT_REMOTE_PATH,
        container_id: str = None
    ):
        """
        Start a container with the specified image. If the container_id is provided, the container will not be started and the existing container will be used.

        Args:
            image_identifier: the identifier of the docker image to use
            workdir: the workspace for all execution sandbox activities
            container_id: the id of the container to use. If provided, the container will not be started and the existing container will be used.
        """
        self.workdir = workdir
        self.container_id = container_id
        self.start(container_id=container_id, image_identifier=image_identifier)

    def get_workdir(self) -> str:
        """
        Get the workdir of the sandbox
        """
        return self.workdir

    def download_artifacts(self, output_dir: str) -> List[str]:
        """
        Download the artifacts from the sandbox to local machine
        
        Args:
            output_dir: Local directory path where artifacts should be downloaded

        Returns:
            List[str]: List of downloaded file names
        """
        if self.container is None:
            raise Exception("Container not started")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the list of files in the workdir
        result = self.container.exec_run(f'ls {self.workdir}')
        files = result.output.decode('utf-8').strip().split('\n')
        
        # Download each file from the container
        downloaded_files = []
        for file in files:
            if file == '':
                continue
                
            try:
                # Get the archive of the file from the container
                bits, _ = self.container.get_archive(f'{self.workdir}/{file}')
                tar_stream = io.BytesIO(b''.join(bits))
                
                # Extract the tar stream to the output directory
                try:
                    with tarfile.open(fileobj=tar_stream) as tar:
                        tar.extractall(path=output_dir)
                finally:
                    tar_stream.close()
                    
                logging.info(f"Downloaded {file} to {output_dir}")
                downloaded_files.append(file)
            except Exception as e:
                logging.error(f"Error downloading file {file}: {e}")

        return downloaded_files

    def start(self, container_id: str = None, image_identifier: str = SANDBOX_IMANGE_IDENTIFIER):
        """
        Start the sandbox
        
        Args:
            container_id: the id of the container to use. If provided, the container will not be started and the existing container will be used.
            image_identifier: the identifier of the docker image to use
        """
        if self.container is not None:
            raise Exception("Container already started")

        client = docker.from_env()
        try:
            container = None
            try:
                if container_id is None:
                    container = client.containers.run(image_identifier, detach=True, network_disabled=False)
                else:
                    container = client.containers.get(container_id)
            except Exception as e:
                logging.error(f"Error starting container: {e}")
                logging.error(f"Container: {container}")
                print(traceback.format_exc())
                raise e

            if (container is not None):
                self.image = container.image
                self.container = container
            else: 
                raise Exception("Container not started")
            
            self.available_files = []
            self.all_artifact_files = []

            # make the workdir
            self.container.exec_run(f'mkdir -p {self.workdir}')

            self.container_id = container.short_id

        finally:
            client.close()

        return self.exists()

    def upload_file(
        self, 
        data: Union[str, bytes, pd.DataFrame] = None,
        local_file_path: str = None, 
        target_file_path: str = None, 
    ) -> bool:
        """
        Upload a file to the docker container from various sources.
        
        This function supports multiple input modes:
        1. From local file: provide local_file_path and target_file_path
        2. From in-memory data: provide data and target_file_path
        
        Args:
            data: In-memory data to upload. Can be:
                  - str: text data
                  - bytes: binary data
                  - pd.DataFrame: will be saved in specified format (csv, parquet, json)
            local_file_path: Path to file on local machine (alternative to data)
            target_file_path: Full path where file should be saved in container (required)
        
        Returns:
            True if the file is uploaded successfully
            
        Raises:
            Exception: If sandbox is not started or invalid arguments provided
            
        Examples:
            # Upload from local file
            sandbox.upload_file(local_file_path="/tmp/data.csv", target_file_path="/workdir/data.csv")
            
            # Upload DataFrame as CSV
            df = pd.DataFrame({'a': [1, 2, 3]})
            sandbox.upload_file(data=df, target_file_path="/workdir/data.csv")
            
            # Upload DataFrame as Parquet
            sandbox.upload_file(data=df, target_file_path="/workdir/data.parquet", df_format='parquet')
            
            # Upload DataFrame as JSON
            sandbox.upload_file(data=df, target_file_path="/workdir/data.json", df_format='json')
            
            # Upload text/string
            sandbox.upload_file(data="Hello World", target_file_path="/workdir/hello.txt")
            
            # Upload bytes
            sandbox.upload_file(data=b"binary data", target_file_path="/workdir/data.bin")
        """
        if self.container is None:
            raise Exception("the sandbox is not started")
        
        if target_file_path is None:
            raise ValueError("target_file_path is required")
        
        # Determine the source of data
        content_bytes: bytes = None
        
        # Priority: data > file_content > local_file_path
        if data is not None:
            # Handle pandas DataFrame
            if isinstance(data, pd.DataFrame):
                buffer = io.BytesIO()
                target_file_path_basename = os.path.basename(target_file_path)
                df_format = target_file_path_basename.split('.')[-1]
                assert df_format in ['csv', 'parquet', 'json'], f"Unsupported DataFrame format: {df_format}. Use 'csv', 'parquet', or 'json'"
                if df_format == 'csv':
                    data.to_csv(buffer, index=False)
                elif df_format == 'parquet':
                    data.to_parquet(buffer, index=False)
                elif df_format == 'json':
                    data.to_json(buffer, orient='records', indent=2)
                content_bytes = buffer.getvalue()
            
            # Handle string
            elif isinstance(data, str):
                content_bytes = data.encode('utf-8')
            
            # Handle bytes
            elif isinstance(data, bytes):
                content_bytes = data
            
            else:
                raise TypeError(f"Unsupported data type: {type(data)}. Must be str, bytes, or pd.DataFrame")
        
        elif local_file_path is not None:
            # Read from local file
            with open(local_file_path, 'rb') as f:
                content_bytes = f.read()
        
        else:
            raise ValueError("Must provide one of: data, file_content, or local_file_path")
        
        # Create a tar archive in memory
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Get the file name from target path
            file_name = os.path.basename(target_file_path)
            
            # Create TarInfo for the file
            tarinfo = tarfile.TarInfo(name=file_name)
            tarinfo.size = len(content_bytes)
            tarinfo.mtime = int(datetime.now().timestamp())
            
            # Add file to tar archive
            tar.addfile(tarinfo, io.BytesIO(content_bytes))
        
        # Get the directory path (without filename) for put_archive
        target_dir = os.path.dirname(target_file_path)
        if not target_dir:
            target_dir = '/'
        
        # Reset stream position and upload
        tar_stream.seek(0)
        self.container.put_archive(target_dir, tar_stream)
        
        return True
        
    def upload_tables(self, dataset: UploadDataset) -> bool:
        """
        place the tables in the dataset into the docker container
        """

        if self.container is None:
            raise Exception("Container not started")

        # write each dataframe to the docker container
        for local_table_path, target_table_path in dataset:
            try:
                # Use the current thread ID and timestamp to create a unique identifier
                unique_id = f"{threading.get_ident()}_{int(datetime.now().timestamp() * 1000)}"

                # step 1: create a temp file on the local machine
                temp_path = f'/tmp/table_{unique_id}'
                
                # copy the local table object to the temp file
                shutil.copy(local_table_path, temp_path)
                
                tar_path = f'/tmp/table_{unique_id}.tar'
                table_name = os.path.basename(target_table_path)
                with tarfile.open(tar_path, 'w') as tar:
                    tar.add(temp_path, arcname=table_name)

                # step 3: copy the tar file to the container **at the target directory**
                with open(tar_path, 'rb') as f:
                    data = f.read()
                    target_folder = os.path.dirname(target_table_path)
                    self.container.put_archive(target_folder, data)

                os.remove(tar_path)
                os.remove(temp_path)

                # Clean up the temporary files after use
                self.available_files.append(target_table_path)
            except Exception as e:
                logging.error(f"Error uploading table {local_table_path} to {target_table_path}: {e}")
                raise e

        return True

    def execute(self, language: str, code: str) -> Tuple[int, str, List[str], float, float]:
        """
        Execute code in the container and extract any resulting files/figures/stdout

        Returns:
            exit_code (int): Exit code of the execution
            stdout (str): Standard output from the execution
            artifacts (List[str]): List of artifact paths ON HOST MACHINE (in `/tmp` directory)
            running_time (float): Running time in seconds during execution
            peak_memory_mb (float): Peak memory consumption in MB during execution
        """
        # generate a filename for the code in the container
        execution_id = uuid.uuid4().hex[:8]

        # copy the code into the container as file
        host_file_path = f'/tmp/{execution_id}_dswiz'
        if (language == "python"):
            host_file_path += '.py'
        elif (language == "r"):
            host_file_path += '.r'

        host_tar_file = f'/tmp/{execution_id}.tar'

        with open(host_file_path, 'w') as f:
            f.write(code)

        arcname = f'{execution_id}'
        if (language == "python"):
            arcname += '.py'
        elif (language == "r"):
            arcname += '.r'

        with tarfile.open(host_tar_file, 'w') as tar:
            tar.add(host_file_path, arcname=arcname)

        self.container.exec_run('mkdir /code')
        with open(host_tar_file, 'rb') as f:
            self.container.put_archive('/code', f)

        os.remove(host_file_path)
        os.remove(host_tar_file)

        # Track peak memory usage during execution
        peak_memory_bytes = [0]  # Use list to allow modification in thread
        memory_monitoring_active = [True]
        start_time = time.time()
        def monitor_memory():
            """Monitor container memory usage in background thread"""
            while memory_monitoring_active[0]:
                try:
                    stats = self.container.stats(stream=False)
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    if memory_usage > peak_memory_bytes[0]:
                        peak_memory_bytes[0] = memory_usage
                except:
                    pass
                # Sample every 100ms
                threading.Event().wait(0.1)
        
        # Start memory monitoring thread
        memory_thread = threading.Thread(target=monitor_memory, daemon=True)
        memory_thread.start()
        
        try:
            if language == "python":
                exit_code, output = self.container.exec_run(
                    f'python /code/{execution_id}.py', workdir=self.workdir)
            elif language == "r":
                exit_code, output = self.container.exec_run(
                    f'Rscript /code/{execution_id}.r', workdir=self.workdir)
        finally:
            # Stop memory monitoring
            memory_monitoring_active[0] = False
            memory_thread.join(timeout=1.0)
        end_time = time.time()
        running_time = end_time - start_time
        new_files = self.container.exec_run(
            f'ls {self.workdir}').output.decode('utf-8').split('\n')

        new_files_set = set()
        for file in new_files:
            if file != '' and (".csv" not in file and ".tsv" not in file and ".txt" not in file):
                new_files_set.add(file)


        # the mechanism for surfacing any artifacts resulting from the execution. 
        # create a new folder in /tmp with the execution_id
        artifacts = []
        host_folder = os.path.join('/tmp', execution_id)
        os.makedirs(host_folder, exist_ok=True)
        
        self.all_artifact_files.append(host_folder) # we need to track this folder so we can remove it later. Otherwise there will be a memory leak.
        
        for file in new_files_set:
            # get the object out of the docker container, and load it to the host file system.
            # the file name should be the same as the one in the container
            host_file_path = os.path.join(host_folder, file)

            # copy from docker container to host file system
            bits, _ = self.container.get_archive(f'{self.workdir}/{file}')
            tar_stream = io.BytesIO(b''.join(bits))

            try:
                with tarfile.open(fileobj=tar_stream) as tar:
                    tar.extractall(path=os.path.dirname(host_file_path))
            finally:
                tar_stream.close()
            
            # track all the files in the host system.
            # when running multiple experiments, this will help us clean up the files.
            artifacts.append(host_file_path)
            self.all_artifact_files.append(host_file_path)

        # decode the output
        output_logs = output.decode('utf-8')

        # implement a truncation in the middle for the output logs
        # using tiktoken to count the tokens and truncate the middle
        output_logs = truncate_middle_tokens(output_logs, 100000)
        
        
        # Convert peak memory to MB for easier reading
        peak_memory_mb = peak_memory_bytes[0] / (1024 * 1024)
        
        return exit_code, output_logs, artifacts, running_time, peak_memory_mb

    def stop(self):
        """
        Stop the docker container and clean up resources
        """
        # try to remove all the files in the all_artifact_files list
        # if we do not remove these, the host machine will run out of disk space
        artifacts_removed = []
        for file in self.all_artifact_files:
            if not os.path.exists(file):
                artifacts_removed.append(file)
                continue
            
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    artifacts_removed.append(file)
                elif os.path.isdir(file):
                    shutil.rmtree(file)
                    
                    if os.path.exists(file):
                        logging.warning(f"Directory still exists after rmtree: {file}")
                        # Try force remove with shell command as fallback
                        os.system(f"rm -rf {file}")
                        
                    artifacts_removed.append(file)
                else:
                    logging.warning(f"File {file} is not a file or directory")
            except Exception as e:
                logging.error(f"Error removing file {file}: {e}")
        
        logging.info(f"Removed {len(artifacts_removed)} artifacts of {len(self.all_artifact_files)}")
        self.all_artifact_files = [
            file for file in self.all_artifact_files if file not in artifacts_removed
        ]
        
        client = docker.from_env()
        try:
            try:
                # Stop and remove container
                # container = client.containers.get(self.container_id)
                # container.stop(timeout=120)
                # container.remove()
                os.system(f"docker kill {self.container_id}")
                # remove the container
                os.system(f"docker rm {self.container_id}")
            except NotFound as e:
                logging.warning(f"Container not found: {e}")
            except Exception as e:
                logging.exception(f"Error stopping container: {e}")
                raise e
            
            # Prune unused volumes
            try:
                client.volumes.prune()
                logging.info("Successfully pruned unused volumes")
            except Exception as e:
                logging.warning(f"Failed to prune volumes: {e}")
                
        finally:
            client.close()

        self.container = None # clear the container reference
        

    def clear_code(self):
        """
        Clear only the code directory in the container
        """
        self.container.exec_run('rm -rf /code')

    def clear_workspace(self):
        """
        Clear the workspace of the docker container while preserving uploaded tables.
        Uses the available_files list to determine which files to preserve.
        """
        # First, clear the code directory
        self.clear_code()
        
        if self.available_files:
            # Create a find command that excludes the specific files we want to preserve
            exclude_patterns = ' '.join([f'! -path "{f}"' for f in self.available_files])
            self.container.exec_run(f'find {self.workdir} -type f {exclude_patterns} -delete')
        else:
            # If no files to preserve, clear everything
            self.container.exec_run(f'rm -rf {self.workdir}/*')

    def exists(self) -> bool:
        """
        Check if the container exists
        """
        return self.container is not None
            
            
if __name__ == "__main__":
    sandbox = ExecutionSandboxWrapper(SANDBOX_IMANGE_IDENTIFIER, DEFAULT_REMOTE_PATH)
    print(sandbox.container.id)