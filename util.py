import os
import hashlib
from filecmp import cmp

def filter_dictionary_by_key(original_dict, key_to_keep):
    # Create a new dictionary with only items that have the specified key
    filtered_dict = {k: v for k, v in original_dict.items() if k == key_to_keep}
    return filtered_dict


def are_files_equal_quick(file1, file2):
    """
    Performs a quick comparison of two files.
    First checks file sizes, then uses filecmp for a shallow comparison.
    
    Returns: True if files appear to be the same, False otherwise
    """
    # First check if file sizes are different (fastest check)
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    
    # If sizes match, use the fast built-in filecmp.cmp() function for shallow comparison
    return cmp(file1, file2, shallow=True)

def are_files_equal_thorough(file1, file2):
    """
    Performs a thorough comparison of two files by comparing file hashes.
    Slower but guarantees correct result.
    
    Returns: True if files are identical, False otherwise
    """
    # First check if file sizes are different (fastest check)
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    
    # Calculate and compare hashes
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        # Use a buffer size of 64kb for efficiency
        BUFFER_SIZE = 65536
        
        hash1 = hashlib.blake2b()
        hash2 = hashlib.blake2b()
        
        while True:
            data1 = f1.read(BUFFER_SIZE)
            data2 = f2.read(BUFFER_SIZE)
            
            if not data1 and not data2:
                break
            if not data1 or not data2 or len(data1) != len(data2):
                return False
                
            hash1.update(data1)
            hash2.update(data2)
            
            # If chunks differ, files are different
            if data1 != data2:
                return False
                
        return hash1.digest() == hash2.digest()


def are_files_equal_balanced(file1, file2):
    """
    A balanced approach:
    1. Check file sizes first (fastest)
    2. Do a quick filecmp comparison which is usually accurate
    3. Fall back to hash comparison only if needed (rare case)
    
    This approach offers the best balance of speed and accuracy.
    """
    # Check if file sizes differ
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    
    # Do a quick comparison first
    if cmp(file1, file2, shallow=True):
        return True
        
    # If quick comparison shows different but sizes match,
    # fall back to hash comparison (rare case where shallow comparison fails)
    return are_files_equal_thorough(file1, file2)