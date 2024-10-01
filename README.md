# Vircadia World Blender Tools

This is a Blender add-on that allows the creation of full Vircadia worlds within Blender, to be exported directly for upload into the server once done.

## Installation

1. Download the latest release from the [releases page](https://github.com/vircadia/vircadia-world-tools/releases).
2. Open Blender and go to `Edit > Preferences > Add-ons`.
3. Click `Install` and select the downloaded folder.
4. Enable the add-on.
5. Make sure your right sidebar is open, if not the hotkey typically is `N` to open it.
6. Navigate to the `Vircadia` tab.

## Requirements

Blender Version 4.2 (LTS) or later.

## Development

Pull this repository recursively to get the submodules.

```bash
git clone --recurse-submodules https://github.com/vircadia/vircadia-world-tools.git
```

If you've already cloned it without the submodules, you can initialize and update them with:

```bash
git submodule update --init --recursive
```

1. Make a 'development-env' venv with python 3.10 or later.
2. Install the dependencies with pip.
3. Run Blender from the command line with the development add-on enabled.

```bash
python3 -m venv development-env
source development-env/bin/activate
pip install -r requirements.txt
```
