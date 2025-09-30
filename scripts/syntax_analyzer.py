import re
import json
import os
from pathlib import Path

def validate_model_output(output, primary_response_content=None):
    # Pattern for content within SEARCH/REPLACE blocks that explicitly excludes block delimiters
    # (?!...) is a negative lookahead assertion.
    # It means "match the current character ONLY IF it is NOT immediately followed by any of these sequences".
    content_no_nested_marker = r"(?:(?!<<<<<<< \s* SEARCH|=======|>>>>>>> \s* REPLACE)[\s\S])*"

    # Pattern for a single SEARCH/REPLACE block
    # Using re.VERBOSE flag (re.X) allows for comments and ignores most whitespace within the regex string.
    # The actual whitespace between parts like `<<<<<<<` and `SEARCH` is explicitly handled by `\s*`.
    search_replace_block_pattern = re.compile(r"""
        <<<<<<< \s* SEARCH \s* # Start of SEARCH block
        (                                                     # Start capturing group for SEARCH content
            """ + content_no_nested_marker + r"""             # The content itself
        )                                                     # End capturing group for SEARCH content
        \s* ======= \s* # Separator
        (                                                     # Start capturing group for REPLACE content
            """ + content_no_nested_marker + r"""             # The content itself
        )                                                     # End capturing group for REPLACE content
        \s* >>>>>>> \s* REPLACE \s* # End of REPLACE block
    """, re.DOTALL | re.VERBOSE)

    # Main regex for the overall output structure
    # Using named groups for clarity: <think_content>, <lgtm>, <sr_blocks>
    # sr_blocks will capture the entire string of concatenated search/replace blocks if present.
    main_regex_str = r"""(?x) # Enable verbose regex for main pattern
        ^ \s* # Optional leading whitespace
        <think> (?P<think_content> [\s\S]*? ) </think>        # Think block content
        \s*
        <final_response> \s*
        (?:                                                   # Non-capturing group for OR logic (lgtm OR sr_blocks)
            (?P<lgtm> lgtm )                                  # Option 1: lgtm
            |                                                 # OR
            (?P<sr_blocks>                                    # Option 2: search/replace blocks (capture the whole string)
                (?: """ + search_replace_block_pattern.pattern + r""") # Reference the raw pattern of the compiled regex
                +                                             # One or more search/replace blocks
            )
        )
        \s* </final_response> \s* $                           # Optional trailing whitespace and end of string
    """
    
    match = re.fullmatch(main_regex_str, output, re.DOTALL | re.VERBOSE)
    
    if not match:
        # Get detailed error information
        error_type = categorize_structure_failure(output)
        error_message = "Overall structure is incorrect."
        return False, {"type": error_type, "message": error_message}

    think_content = match.group("think_content").strip()
    lgtm_content = match.group("lgtm")
    sr_blocks_string = match.group("sr_blocks") 

    search_values = []

    if lgtm_content:
        if sr_blocks_string: 
            return False, {"type": "both_lgtm_and_sr_blocks", "message": "Contains both 'lgtm' and search/replace blocks."}
    elif sr_blocks_string:
        # If search/replace blocks are present, extract the search contents
        # Use the pre-compiled search_replace_block_pattern to find all blocks
        for sr_match in search_replace_block_pattern.finditer(sr_blocks_string):
            search_content = sr_match.group(1).strip() # group(1) is the SEARCH content
            search_values.append(search_content)
            
            # Check if search content exists in primary response
            if primary_response_content and search_content:
                if search_content not in primary_response_content:
                    return False, {"type": "search_content_not_found", "message": f"Search content not found in primary response: '{search_content[:50]}{'...' if len(search_content) > 50 else ''}'"}
    else:
        return False, {"type": "neither_lgtm_nor_sr_blocks", "message": "Final response content is neither 'lgtm' nor search/replace blocks."}

    return True, search_values

def categorize_structure_failure(output):
    """Categorize the type of structure failure in the output."""
    # Check for basic structure elements
    has_think_start = "<think>" in output
    has_think_end = "</think>" in output
    has_final_response_start = "<final_response>" in output
    has_final_response_end = "</final_response>" in output
    
    # Check for content types
    has_lgtm = "lgtm" in output.lower()
    has_search_replace = "<<<<<<<" in output and "=======" in output and ">>>>>>>" in output
    
    # Categorize the failure
    if not has_think_start or not has_think_end:
        return "missing_think_tags"
    elif not has_final_response_start or not has_final_response_end:
        return "missing_final_response_tags"
    elif has_lgtm and has_search_replace:
        return "both_lgtm_and_sr_blocks"
    elif not has_lgtm and not has_search_replace:
        return "neither_lgtm_nor_sr_blocks"
    else:
        return "other_structure_error"


def analyze_trajectory_file(file_path):
    """Analyze a single trajectory file and return accuracy statistics."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        refiner_outputs = []
        total_refiner_outputs = 0
        valid_refiner_outputs = 0
        error_buckets = {
            "missing_think_tags": 0,
            "missing_final_response_tags": 0,
            "both_lgtm_and_sr_blocks": 0,
            "neither_lgtm_nor_sr_blocks": 0,
            "search_content_not_found": 0,
            "other_structure_error": 0
        }
        error_messages = {
            "missing_think_tags": "Missing <think> or </think> tags",
            "missing_final_response_tags": "Missing <final_response> or </final_response> tags", 
            "both_lgtm_and_sr_blocks": "Contains both 'lgtm' and search/replace blocks",
            "neither_lgtm_nor_sr_blocks": "Final response content is neither 'lgtm' nor search/replace blocks",
            "search_content_not_found": "Search content not found in primary response",
            "other_structure_error": "Other structure errors"
        }
        
        # Extract refiner outputs from the trajectory
        # Data is a list of items, each with a 'traj' field
        if isinstance(data, list):
            for item in data:
                if 'traj' in item:
                    for step in item['traj']:
                        if step.get('role') == 'assistant' and 'metadata' in step:
                            metadata = step['metadata']
                            if 'refiner_output' in metadata:
                                refiner_output = metadata['refiner_output']
                                total_refiner_outputs += 1
                                
                                # Get primary response content for validation
                                primary_response_content = None
                                if 'primary_response' in metadata and 'content' in metadata['primary_response']:
                                    primary_response_content = metadata['primary_response']['content']
                                
                                # Validate the refiner output
                                is_valid, extracted_data = validate_model_output(refiner_output, primary_response_content)
                                refiner_outputs.append({
                                    'output': refiner_output,
                                    'is_valid': is_valid,
                                    'extracted_data': extracted_data
                                })
                                
                                if is_valid:
                                    valid_refiner_outputs += 1
                                else:
                                    # Categorize the error
                                    if isinstance(extracted_data, dict) and "type" in extracted_data:
                                        error_type = extracted_data["type"]
                                        error_message = extracted_data["message"]
                                    else:
                                        # Fallback for old format or unexpected data
                                        error_type = "unknown_error"
                                        error_message = str(extracted_data)
                                    
                                    if error_type in error_buckets:
                                        error_buckets[error_type] += 1
                                    else:
                                        error_buckets["other_structure_error"] += 1
        
        accuracy = valid_refiner_outputs / total_refiner_outputs if total_refiner_outputs > 0 else 0
        
        return {
            'file_path': str(file_path),
            'total_refiner_outputs': total_refiner_outputs,
            'valid_refiner_outputs': valid_refiner_outputs,
            'accuracy': accuracy,
            'refiner_outputs': refiner_outputs,
            'error_buckets': error_buckets,
            'error_messages': error_messages
        }
    
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return {
            'file_path': str(file_path),
            'total_refiner_outputs': 0,
            'valid_refiner_outputs': 0,
            'accuracy': 0,
            'refiner_outputs': [],
            'error_buckets': {},
            'error_messages': {},
            'error': str(e)
        }

def analyze_all_trajectories(trajectories_dir):
    """Analyze all trajectory files in the given directory and subdirectories."""
    trajectories_path = Path(trajectories_dir)
    
    if not trajectories_path.exists():
        print(f"Directory {trajectories_dir} does not exist")
        return
    
    # Find all JSON files in the trajectories directory
    json_files = list(trajectories_path.rglob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {trajectories_dir}")
        return
    
    print(f"Found {len(json_files)} JSON files to analyze")
    print("=" * 80)
    
    all_results = []
    total_files = len(json_files)
    total_refiner_outputs = 0
    total_valid_outputs = 0
    total_error_buckets = {
        "missing_think_tags": 0,
        "missing_final_response_tags": 0,
        "both_lgtm_and_sr_blocks": 0,
        "neither_lgtm_nor_sr_blocks": 0,
        "search_content_not_found": 0,
        "other_structure_error": 0
    }
    error_messages = {
        "missing_think_tags": "Missing <think> or </think> tags",
        "missing_final_response_tags": "Missing <final_response> or </final_response> tags", 
        "both_lgtm_and_sr_blocks": "Contains both 'lgtm' and search/replace blocks",
        "neither_lgtm_nor_sr_blocks": "Final response content is neither 'lgtm' nor search/replace blocks",
        "search_content_not_found": "Search content not found in primary response",
        "other_structure_error": "Other structure errors"
    }
    
    for i, file_path in enumerate(json_files, 1):
        print(f"Analyzing file {i}/{total_files}: {file_path.name}")
        
        result = analyze_trajectory_file(file_path)
        all_results.append(result)
        
        total_refiner_outputs += result['total_refiner_outputs']
        total_valid_outputs += result['valid_refiner_outputs']
        
        # Aggregate error buckets
        for error_type, count in result['error_buckets'].items():
            total_error_buckets[error_type] += count
        
        print(f"  - Refiner outputs: {result['total_refiner_outputs']}")
        print(f"  - Valid outputs: {result['valid_refiner_outputs']}")
        print(f"  - Accuracy: {result['accuracy']:.3f}")
        if 'error' in result:
            print(f"  - Error: {result['error']}")
        else:
            # Show error breakdown for this file
            invalid_outputs = result['total_refiner_outputs'] - result['valid_refiner_outputs']
            if invalid_outputs > 0:
                print(f"  - Error breakdown:")
                for error_type, count in result['error_buckets'].items():
                    if count > 0:
                        error_desc = result.get('error_messages', {}).get(error_type, error_type)
                        print(f"    * {error_desc}: {count}")
        print()
    
    # Calculate overall statistics
    overall_accuracy = total_valid_outputs / total_refiner_outputs if total_refiner_outputs > 0 else 0
    
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print(f"Total files analyzed: {total_files}")
    print(f"Total refiner outputs: {total_refiner_outputs}")
    print(f"Total valid outputs: {total_valid_outputs}")
    print(f"Overall accuracy: {overall_accuracy:.3f}")
    print()
    
    # Error bucket summary
    total_invalid_outputs = total_refiner_outputs - total_valid_outputs
    if total_invalid_outputs > 0:
        print("ERROR BREAKDOWN:")
        print("-" * 60)
        for error_type, count in total_error_buckets.items():
            if count > 0:
                percentage = (count / total_invalid_outputs) * 100
                error_desc = error_messages.get(error_type, error_type)
                print(f"{error_desc:<45} | {count:>6} ({percentage:>5.1f}%)")
        print()
    
    # Per-file breakdown
    print("PER-FILE BREAKDOWN:")
    print("-" * 80)
    for result in all_results:
        file_name = Path(result['file_path']).name
        print(f"{file_name:<60} | {result['accuracy']:.3f} ({result['valid_refiner_outputs']}/{result['total_refiner_outputs']})")
    
    return all_results

if __name__ == "__main__":
    # Analyze all trajectory files
    trajectories_directory = "/Users/meyceoz/Downloads/trajectories"
    results = analyze_all_trajectories(trajectories_directory)

