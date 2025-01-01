#!/usr/bin/env -S blender --factory-startup --background --enable-autoexec --python-exit-code 1 --python
"""
Script for setting up Blender preferences.

- Use Cycles with CUDA GPU
- Enable Node Wrangler addon
- Download and enable NodeToPython addon
"""

import os
import urllib.request

import bpy


def main():
    # Configure Cycles for GPU rendering
    context: bpy.types.Context = bpy.context  # type: ignore
    cycles_preferences = context.preferences.addons["cycles"].preferences
    cycles_preferences.compute_device_type = "CUDA"  # type: ignore
    cycles_preferences.get_devices()  # type: ignore
    for device in cycles_preferences.devices:  # type: ignore
        device.use = device.type == "CUDA"

    # Set the render engine to Cycles
    scene: bpy.types.Scene = context.scene
    scene.cycles.device = "GPU"
    scene.render.engine = "CYCLES"  # type: ignore

    # Enable Node Wrangler
    bpy.ops.preferences.addon_enable(module="node_wrangler")

    # Download, install and enable NodeToPython
    addon_name = "NodeToPython"
    addon_url = "https://github.com/BrendanParmer/NodeToPython/releases/download/v3.3.0/NodeToPython.zip"
    download_path = os.path.join(bpy.app.tempdir, f"{addon_name}.zip")
    urllib.request.urlretrieve(addon_url, download_path)
    bpy.ops.preferences.addon_install(filepath=download_path)
    bpy.ops.preferences.addon_enable(module=addon_name)
    os.remove(download_path)

    # Save preferences
    bpy.ops.wm.save_userpref()


if __name__ == "__main__":
    main()
