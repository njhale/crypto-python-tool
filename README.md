## Writing your first tool in Python

[python-crypto-tool](https://github.com/otto8-ai/python-crypto-tool) showcases how a `Python` implementation of the `Hash` example Tool.

This guide below walks through the structure and design of the Tool and calls out the requirements to package it for use by [Otto8 Agents](https://docs.otto8.ai/concepts/agents)

To clone this repo and follow along, run the following command:

```bash
git clone git@github.com/otto8-ai/python-crypto-tool
```

### Tool Repo Structure

The directory tree below shows the set of files required to package and run `Hash` the Tool in `Otto8`.

```
python-crypto-tool
├── hash.py
├── requirements.txt
└── tool.gpt
```

### Defining the `Hash` Tool

Every Tool repository must have a `tool.gpt` file in its root directory.

The `tool.gpt` file contains [GPTScript Tool Definitions](https://docs.gptscript.ai/tools/gpt-file-reference) which describe a set of Tools that
can be used by Agents in `Otto8`.

Every Tool has a descriptive `Name` and `Description` that helps Agent understand what the Tool
does, what it returns (if anything), and any `Parameters` it takes. Agents use these details
to figure out when and how to use the Tool. This section of a tool definition is referred to as
the Tool's `Preamble`.

We want the `Hash` Tool to return the hash of some given `data`. It would also be nice to support a
few different hash algorithms for the Agent to choose from.

Let's take a look at the definition of `Hash` in `tool.gpt` to see how that's achieved:

```text
Name: Hash
Description: Generate a hash of data using the given algorithm and return the result as a hexadecimal string
Param: data: The data to hash
Param: algo: The algorithm to generate a hash with. Supports "sha256" and "md5". Default is "sha256"
```

The `Preamble` above declares a Tool named `Hash`.
The `Param` fields enumerate the arguments that an Agent must provide when calling `Hash`, `data` and `algo`.
In this case, the description of the `algo` parameter also explains what values are allowed (`sha256` or `md5`) and points out
what the default is if the argument isn't provided (`sha256`)
The `Description` explains what `Hash` returns with respect to the given arguments; the hash of `data` using the algorithm selected with `algo`.

Immediately below the `Preamble` is the `Tool Body`, which tells `Otto8` how to execute the Tool:

```text
 #!/usr/bin/env python3 ${GPTSCRIPT_TOOL_DIR}/hash.py
```

The line above is where the magic happens.

Oversimplifying a bit, when an Agent calls the `Hash` Tool, `Otto8` -- by way of `GPTScript` -- reads this line, downloads the appropriate `Python` tool chain, installs the dependencies from the `requirements.txt` if present, projects the call arguments onto environment variables (`DATA` and `ALGO`), then runs `python3 ${GPTSCRIPT_TOOL_DIR}/hash.py`.

Putting it all together, here's the complete definition of the `Hash` Tool.

```text
Name: Hash
Description: Generate a hash of data using the given algorithm and return the result as a hexadecimal string
Param: data: The data to hash
Param: algo: The algorithm to generate a hash with. Default is "sha256". Supports "sha256" and "md5".
#!/usr/bin/env python3 ${GPTSCRIPT_TOOL_DIR}/hash.py
```

### Implementing the Python executed by the `Hash` Tool

The `hash.py` file executed by the `Tool Body` is the concrete implementation of the `Hash` Tool.

Let's walk through the code to understand how it works.

Starting at the bottom, the `main` function is called in a `try` block so that any runtime exceptions
caught are written to stdout. This is important because everything written to stdout is returned
to the Agent when the Tool call is completed, while everything written to stderr is discarded.

```python
if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        # Print err to stdout to return the error to the agent
        print(f'Error: {err}')
        sys.exit(1)
```

Using this pattern ensures that, if a Tool call fails, the calling Agent is informed about the failure.

Moving on, the `main` function implements the meat and potatoes of the `Hash` Tool. It begins by extracting the Tool arguments from the respective environment variables and validates them. If any of the arguments are invalid, execution stops and exceptions are raised that describe the issue in detail. The goal is to provide useful information that an Agent can use to construct valid arguments for subsequent calls. For example, when an unsupported `algo` argument is provided, the code returns an error that contains the complete list of valid algorithms.

```python
SUPPORTED_HASH_ALGORITHMS = ['sha256', 'md5']

def main():
    # Extract the tool's `data` argument from the env
    data = os.getenv('DATA')
    if not data:
        raise ValueError('A data argument must be provided')

    # Extract the tool's `algo` argument from the env and default to `sha256`
    algo = os.getenv('ALGO', 'sha256')
    if algo not in SUPPORTED_HASH_ALGORITHMS:
        # Return the supported algorithms in the error message to help agents choose a valid
        # algorithm the next time they call this tool
        raise ValueError(f'Unsupported hash algorithm: {algo} not in {SUPPORTED_HASH_ALGORITHMS}')
    #...
```

After validating the arguments, the hash is calculated and JSON is written to stdout containing the hash along with the algorithm used to generate it. Providing extra contextual info -- e.g. the algorithm used -- with the result in a structured format is a considered best practice. It's a pattern that improves the Agent's ability to correctly use the result.

```python
    # ...
    # Generate the hash
    hash_obj = hashlib.new(algo)
    hash_obj.update(data.encode('utf-8'))

    # Return the hash along with the algorithm used to generate it.
    # Providing more information in the tool's response makes it easier for agents to keep
    # track of the context.
    print(json.dumps({
        'algo': algo,
        'hash': hash_obj.hexdigest()
    }))
```

### Complete `hash.py`

See the content of the complete `hash.py` below:

```python
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
```

### Otto8 Metadata

The `tool.gpt` file also provides some additional metadata for the to `Otto8`.

The two most important bits of metadata are:

1. `!metadata:*:category` which tags Tools with the `Crypto` category to promote organization and discovery
2. `!metadata:*:icon` which assigns `https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/duotone/fingerprint-duotone.svg` as the Tool icon

```text
---
!metadata:*:category
Crypto

---
!metadata:*:icon
https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/duotone/fingerprint-duotone.svg
```

**Note:** `*` is a wild card pattern that applies the metadata to all Tools defined in `tool.gpt`. We can apply metadata to a specific Tool by either specifying the exact name (e.g. `!metadata:Hash:category`) or adding the metadata directly to a Tool's `Preamble`; e.g.

```text
Name: Hash
Metadata: category: Crypto
Metadata: icon: https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/duotone/fingerprint-duotone.svg
```

### Otto8 Tool Bundles

`Tool Bundles` provide a mechanism to ship a set of Tools together as unified suite. When an Agent imports a `Tool Bundle` it gets access to all of the Tools shared by the Bundle.

Since this repo only defines a single Tool, it doesn't provide much value, but declaring a Bundle up front is a convention that will make it easier for Agent authors to discover and play with new Tools as they are released.

A Bundle is nothing more than another Tool -- typically named after the category -- that shares the set of Tools from `tool.gpt` to be bundled together, and is marked with `Metadata: bundle: true`.

**Note:** There can only be one Bundle Tool per `tool.gpt`.

```text
---
Name: Crypto
Metadata: bundle: true
Description: Tools providing common cryptographic functions
Share Tools: Hash
```

### Complete `tool.gpt`

See the content of the complete `tool.gpt` below:

```text
---
Name: Crypto
Metadata: bundle: true
Description: Tools providing common cryptographic functions
Share Tools: Hash

---
Name: Hash
Description: Generate a hash of data using the given algorithm and return the result as a hexadecimal string
Param: data: The data to hash
Param: algo: The algorithm to generate a hash with. Supports "sha256" and "md5". Default is "sha256"

#!/usr/bin/env python3 ${GPTSCRIPT_TOOL_DIR}/hash.py

---
!metadata:*:category
Crypto

---
!metadata:*:icon
https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/duotone/fingerprint-duotone.svg
```

### Running `hash.py` Locally

Under the hood, `Otto8` will use `venv` to set up a virtual environment and install any dependencies listed in the `requirements.txt` before executing `#!/usr/bin/env python3 ${GPTSCRIPT_TOOL_DIR}/hash.py`, so it's a good habit to verify this works on your machine before trying it out in `Otto8`.

To do this, run through the following steps in the root of your local fork:

1. Set up a virtual environment in the root of your local fork:

```bash
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Install and freeze dependencies (not necessary for this Tool since it doesn't have any external dependencies):

```bash
pip install -r requirements.txt
pip freeze > requirements.txt
```

4. Run `hash.py` against with some test arguments

```bash
DATA='foo' python3 hash.py
```

```json
{
  "algo": "sha256",
  "hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
}
```

```bash
python3 hash.py
```

```text
Error: A data argument must be provided
```

```bash
DATA='foo' ALGO='md5' python3 hash.py
```

```json
{ "algo": "md5", "hash": "acbd18db4cc2f85cedef654fccc4a4d8" }
```

```bash
DATA='foo' ALGO='whirlpool' python3 hash.py
```

```text
Error: Unsupported hash algorithm: whirlpool not in ['sha256', 'md5']
```

### Adding Tools to `Otto8`

Before a Tool can be imported by an agent, it needs to be added to `Otto8`.

To add a Tool, have a user with admin privileges:

1. Navigate to the `Otto8` admin UI in a browser and open the Tools page by clicking the "Tools" button in the left drawer
   ![Open The Tools Page](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/add-tools-step-0.png "Open The Tools Page")
2. Click the "Register New Tool" button on the right
   ![Click The Register New Tool Button](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/add-tools-step-1.png "Click The Register New Tool Button")
3. Type the Tool repo reference into the modal's input box -- in this example `github.com/otto8-ai/python-crypto-tool` -- and click "Register Tool"
   ![Enter Tool Repo Reference](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/add-tools-step-2.png "Enter Tool Repo Reference")

After running through the steps above, the Tools will be available for use in `Otto8`.

You can search for the Tools by category or name on the Tools page to verify:

![Search For Newly Added Tools](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/add-tools-step-3.png "Search For Newly Added Tools")

### Using The `Hash` Tool in `Otto8`

After adding the Tool to `Otto8`, it's now ready to be imported by an Agent.

To try it out, open the Edit page for an Agent you want to add the `Hash` Tool to, then:

1. Click the "Add Tool" button under either the "Agent Tools" or "User Tools" sections
   ![Click The Add Tool Button](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/use-tools-step-0.png "Click The Add Tool Button")
2. Search for "Hash" or "Crypto" in the Tool search pop-out and select the `Hash` Tool or flip the toggle to the right of `Crypto` to add all Tools in the `Crypto` Bundle (which is only `Hash` for now)
   ![Add Hash Tool To Agent](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/use-tools-step-1.png "Add Hash Tool To Agent")
   ![Add Crypto Bundle To Agent](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/use-tools-step-2.png "Add Crypto Bundle To Agent")
3. Ask the Agent to generate a hash
   ![Ask The Agent To Generate a Hash](https://raw.githubusercontent.com/otto8-ai/python-crypto-tool/refs/heads/main/docs/use-tools-step-3.png "Ask The Agent To Generate a Hash")
