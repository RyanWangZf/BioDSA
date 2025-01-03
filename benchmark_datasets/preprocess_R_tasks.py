import pdb
import sys, os
def setup_environment():
    REPO_BASE_DIR  = "/home/ubuntu/dscodegen_submission_code"
    os.environ["REPO_BASE_DIR"] = REPO_BASE_DIR
    sys.path.append(REPO_BASE_DIR)

if __name__ == "__main__":
    # setup 
    setup_environment()
    from src.data_schema_mapper import VanillaMapper, TCGADataSchemaMapper
    from benchmark_evaluation.utils import load_all_R_samples

    # load the data and build the inputs
    REPO_BASE_DIR = os.getenv("REPO_BASE_DIR")
    data_input_dir = f"{REPO_BASE_DIR}/benchmark_datasets/R/datasets"
    query_data_path = f"{REPO_BASE_DIR}/benchmark_datasets/R/query_data.xlsx"
    studies = ['23502430', '30828567', '32211396', '32721879', '33176622', '33591944', '33746977', '33795528', '34238253', '34565373', '35222524', '37255653', '38342795',
        '29340250', '31010415', '32637351', '32793288', '33177247', '33597971', '33761933', '34092242', '34305920', '34621245', '37091789', '38329437']
    schema_mapper = TCGADataSchemaMapper()
    samples = load_all_R_samples(
        data_input_dir=data_input_dir, # patient data input path
        query_data_path=query_data_path, # data science task input path
        studies=studies,
        schema_mapper=schema_mapper,
        combine_dataframes=True
    )
    samples.to_csv(f"{REPO_BASE_DIR}/benchmark_datasets/R/coding_tasks.csv", index=False)
    print(samples.iloc[0])
    