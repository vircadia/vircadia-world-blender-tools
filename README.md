# Vircadia World Blender Tools

This is a Blender add-on that allows the creation of full Vircadia worlds within Blender, to be exported directly for upload into the server once done.

## Installation

1. Download the latest release from the [releases page](https://github.com/vircadia/vircadia-world-tools/releases).
1. Open your Blender scripting console and run the following command:
```python
import sys
print(sys.executable)
```
1. This will print the path to your Python executable. Now, with that path, run the following command:
```python
/path/to/blender/python -m pip install supabase
```
1. Confirm that it was installed correctly by running in your Blender scripting console:
```python
import supabase
print(supabase.__version__)
```
1. In Blender, go to `Edit > Preferences > Add-ons`.
1. Click `Install` and select the downloaded folder.
1. Enable the add-on.
1. Make sure your right sidebar is open, if not the hotkey typically is `N` to open it.
1. Navigate to the `Vircadia` tab.

## Development

### Requirements

* Blender Version 4.2 (LTS) or later. (accessible via path as "`blender`")
* Python 3.12
* pip (usually comes with Python)

### Steps

1. Clone this repository recursively to get the submodules:

```bash
git clone --recurse-submodules https://github.com/vircadia/vircadia-world-tools.git
```

If you've already cloned it without the submodules, you can initialize and update them with:

```bash
git submodule update --init --recursive
```

2. Navigate to the project directory:

```bash
cd vircadia-world-tools
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

4. Install the project dependencies:

```bash
pip install -r requirements.txt
```

