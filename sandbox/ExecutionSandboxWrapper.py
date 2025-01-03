import io
import os
import tarfile
import traceback
from typing import List, Tuple
import uuid
import docker
import threading
from datetime import datetime

from sandbox.EvalDatasetLoader import EvalDataset


class ExecutionSandboxWrapper:

    def __init__(self, image_identifier: str, target_dir: str):
        """
        Start a container with the specified image

        `target_dir` is the workspace for all execution sandbox activities. 
        This variable needs to be set on initialization, since all the sandbox functions require this path.
        If this path changes at some point while using this API, then operations like `start` and `execute` will fail.
        """
        client = docker.from_env()

        container = None
        try:
            container = client.containers.run(
                image_identifier, detach=True, network_disabled=False)
        except Exception as e:
            print(f"Error starting container: {e}")
            print(f"Container: {container}")
            print(traceback.format_exc())

        self.target_dir = target_dir

        if (container is not None):
            self.image = container.image
            self.container = container

            # initialize the container workspace
            self.container.exec_run(f'mkdir -p {self.target_dir}')
        else:
            raise Exception("Error starting container")

    def start(self, dataset: EvalDataset) -> Tuple[str]:
        """
        Start the container with the specified dataframes. The dataframes will be saved to the target_dir.

        Returns the paths of the tables inside the docker container
        """

        if self.container is None:
            raise Exception("Container not started")

        # write each dataframe to the docker container
        target_file_names = []
        for name, table in dataset.tables.items():
            # Use the current thread ID and timestamp to create a unique identifier
            unique_id = f"{threading.get_ident()}_{int(datetime.now().timestamp() * 1000)}"

            # step 1: write the table to a temp file with a unique name
            temp_path = f'/tmp/table{name}_{unique_id}'
            with open(temp_path, 'w') as f:
                f.write(table.to_csv(index=False))

            # step 2: to copy the file into the docker, you must create a tar file with the temp file
            tar_path = f'/tmp/table_{unique_id}.tar'
            target_file_name = name
            with tarfile.open(tar_path, 'w') as tar:
                tar.add(temp_path, arcname=target_file_name)

            # step 3: copy the tar file to the container at the target dir
            with open(tar_path, 'rb') as f:
                self.container.put_archive(self.target_dir, f)

            target_file_names.append(os.path.join(self.target_dir, target_file_name))

            # Clean up the temporary files after use
            os.remove(temp_path)
            os.remove(tar_path)

        return target_file_names

    def execute(self, language: str, code: str) -> Tuple[int, str, List[str]]:
        """
        get the dataframes and extract any resulting files/figures/stdout

        Returns the exit code, stdout, and a list of artifact paths ON HOST MACHINE.

        Artifacts are in the `/tmp` directory of the host machine
        """
        # generate a filename for the code in the container
        execution_id = uuid.uuid4().hex

        # copy the code into the container as file
        host_file_path = f'/tmp/{execution_id}'
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

        # clear existing files in the working directory so we can detect changes
        workdir = "/workdir"

        # Clear the workdir
        # # delete any files from the workdir that is not a tsv or csv file
        # self.container.exec_run(f'find {workdir} -type f ! \( -name "*.csv" -o -name "*.tsv" \) -delete')

        # container.exec_run(f'rm -rf {workdir}')
        # container.exec_run(f'mkdir -p {workdir}')

        if language == "python":
            exit_code, output = self.container.exec_run(
                f'python /code/{execution_id}.py', workdir=workdir)
        elif language == "r":
            exit_code, output = self.container.exec_run(
                f'Rscript /code/{execution_id}.r', workdir=workdir)

        new_files = self.container.exec_run(
            f'ls {workdir}').output.decode('utf-8').split('\n')

        new_files_set = set()
        for file in new_files:
            if file != '' and (".csv" not in file and ".tsv" not in file):
                new_files_set.add(file)

        # create a new folder in /tmp with the execution_id
        artifacts = []

        for file in new_files_set:
            # get the object out of the docker container, and load it to the host file system.
            # the file name should be the same as the one in the container
            # add the path of the object in the host machine to the list
            host_file_path = f'/tmp/{execution_id}/{file}'
            os.makedirs(os.path.dirname(host_file_path), exist_ok=True)

            # get the file from the container
            bits, _ = self.container.get_archive(f'{workdir}/{file}')
            tar_stream = io.BytesIO(b''.join(bits))

            with tarfile.open(fileobj=tar_stream) as tar:
                tar.extractall(path=os.path.dirname(host_file_path))
            artifacts.append(host_file_path)

        return exit_code, output, artifacts

    def stop(self):
        """
        Stop the docker container
        """
        client = docker.from_env()
        container = client.containers.get(self.container.id)
        container.stop()
        container.remove()

    def start_deprecated(self, dataset: EvalDataset) -> Tuple[str]:
        """
        DEPRECATED: (do not consider multiple threads issues)
        Start the container with the specified dataframes. The dataframes will be saved to the target_dir.

        Returns the paths of the tables inside the docker container
        """

        if self.container is None:
            raise Exception("Container not started")

        # write each dataframe to the docker container
        target_file_names = []
        for name, table in dataset.tables.items():

            # step 1: write the table to a temp file
            temp_path = '/tmp/table' + name
            with open(temp_path, 'w') as f:
                f.write(table.to_csv(index=False))

            # step 2: to copy the file into the docker, you must create a tar file with the temp file
            target_file_name = name
            with tarfile.open('/tmp/table.tar', 'w') as tar:
                tar.add(temp_path, arcname=target_file_name)

            # step 3: copy the tar file to the container at the target dir
            with open('/tmp/table.tar', 'rb') as f:
                self.container.put_archive(self.target_dir, f)

            target_file_names.append(os.path.join(
                self.target_dir, target_file_name))

        os.remove(temp_path)
        os.remove('/tmp/table.tar')

        return target_file_names