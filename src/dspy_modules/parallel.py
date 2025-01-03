# make batch call for dspy modules
import multiprocessing
import concurrent.futures

def call_module_with_dict(args_dict, dspy_module):
    return dspy_module(**args_dict)

def call_wrapper(args_dict, dspy_module):
    return call_module_with_dict(args_dict, dspy_module)

def batch_call_dspy_module(batch_inputs: list[dict], dspy_module):
    # Determine the number of threads to use
    num_threads = min(multiprocessing.cpu_count(), len(batch_inputs))

    # Include indices in the batch arguments
    batch_args = [(index, inputs) for index, inputs in enumerate(batch_inputs)]
    
    # Use ThreadPoolExecutor to parallelize the API calls
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(call_wrapper, inputs, dspy_module): index for index, inputs in batch_args}
    
    # Initialize a list to store responses in the correct order
    responses = [None] * len(batch_inputs)
    
    for future in concurrent.futures.as_completed(futures):
        index = futures[future]
        try:
            responses[index] = future.result()
        except Exception as exc:
            print(f'Generated an exception: {exc}')
            responses[index] = None
    
    return responses