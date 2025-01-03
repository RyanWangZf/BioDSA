import sys, os
import pdb
def setup_environment():
    REPO_BASE_DIR  = "/home/ubuntu/dscodegen_submission_code"
    os.environ["REPO_BASE_DIR"] = REPO_BASE_DIR
    sys.path.append(REPO_BASE_DIR)

if __name__ == "__main__":
    # setup 
    setup_environment()
    from src.data_schema_mapper import VanillaMapper, TCGADataSchemaMapper
    from benchmark_evaluation.utils import load_all_samples

    # load the data and build the inputs
    REPO_BASE_DIR = os.getenv("REPO_BASE_DIR")
    data_input_dir = f"{REPO_BASE_DIR}/benchmark_datasets/python/datasets"
    query_data_path = f"{REPO_BASE_DIR}/benchmark_datasets/python/query_data.xlsx"
    studies = ["28472509", "32864625", "25303977", "29713087", "28985567", "34819518", "32437664", "37699004", "30742119", "30867592", "33765338"]
    schema_mapper = TCGADataSchemaMapper()
    samples = load_all_samples(
        data_input_dir=data_input_dir, # patient data input path
        query_data_path=query_data_path, # data science task input path
        studies=studies,
        schema_mapper=schema_mapper,
        combine_dataframes=True
    )
    samples.to_csv(f"{REPO_BASE_DIR}/benchmark_datasets/python/coding_tasks.csv", index=False)
    print(samples.iloc[0])
    