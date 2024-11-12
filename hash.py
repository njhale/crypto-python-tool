import hashlib
import json
import os
import sys

SUPPORTED_HASH_ALGORITHMS = ['sha256', 'md5']


def main():
    # Extract the tool's `data` argument from the env
    data = os.getenv('DATA')
    if not data:
        raise ValueError('A data argument must be provided')

    # Extract the tool's `algo` argument from the env and default to `sha256`
    algo = os.getenv('ALGO', 'sha256')
    if algo not in SUPPORTED_HASH_ALGORITHMS:
        # Return the supported algorithms in the error message to help assistants choose a valid
        # algorithm the next time they call this tool
        raise ValueError(f'Unsupported hash algorithm: {algo} not in {SUPPORTED_HASH_ALGORITHMS}')

    # Generate the hash
    hash_obj = hashlib.new(algo)
    hash_obj.update(data.encode('utf-8'))

    # Return the hash along with the algorithm used to generate it.
    # Providing more information in the tool's response makes it easier for assistants to keep
    # track of the context.
    print(json.dumps({
        'algo': algo,
        'hash': hash_obj.hexdigest()
    }))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        # Print err to stdout to return the error to the assistant
        print(f'Error: {err}')
        sys.exit(1)
