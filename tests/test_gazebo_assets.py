import ast
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
GAZEBO = ROOT / "src/simulation/rlai_gazebo"
MODELS = GAZEBO / "models"
WORLDS = GAZEBO / "worlds"
GAZEBO_LAUNCH = GAZEBO / "launch/gazebo.launch.py"
BRINGUP_LAUNCH = ROOT / "src/bringup/rlai_bringup/launch/simulation.launch.py"

EXPECTED_MODELS = {
    "warehouse_shelf",
    "warehouse_pallet",
    "warehouse_pallet_jack",
    "warehouse_box_cluster",
    "warehouse_trash_bin",
    "warehouse_floor_marking",
    "charging_dock",
}

EXPECTED_WORLDS = {
    "demo_warehouse_visual.sdf",
    "benchmark_warehouse_easy.sdf",
    "benchmark_warehouse_medium.sdf",
    "benchmark_warehouse_hard.sdf",
}


def read(path):
    return path.read_text(encoding="utf-8")


def parse_xml(path):
    return ET.parse(path).getroot()


def parse_python(path):
    return ast.parse(read(path))


def string_constants(tree):
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def called_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name is not None:
                names.add(name)
    return names


def is_call(node, name):
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == name
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == name
    return False


def is_launch_config_call(node, key_name):
    if not is_call(node, "LaunchConfiguration") or not node.args:
        return False
    first_arg = node.args[0]
    return (
        isinstance(first_arg, ast.Constant)
        and isinstance(first_arg.value, str)
        and first_arg.value == key_name
    )


def dict_has_launch_config_mapping(node, key_name):
    if not isinstance(node, ast.Dict):
        return False
    for key, value in zip(node.keys, node.values):
        if not (
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and key.value == key_name
        ):
            continue
        if is_launch_config_call(value, key_name):
            return True
    return False


def name_loads(node, target_name):
    return (
        isinstance(node, ast.Name)
        and isinstance(node.ctx, ast.Load)
        and node.id == target_name
    )


def include_launch_forwards_arg(tree, key_name):
    assigned_dicts = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and dict_has_launch_config_mapping(node.value, key_name):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned_dicts.add(target.id)
        elif isinstance(node, ast.AnnAssign) and dict_has_launch_config_mapping(
            node.value, key_name
        ):
            if isinstance(node.target, ast.Name):
                assigned_dicts.add(node.target.id)

    def forwards_launch_config_mapping(value):
        if dict_has_launch_config_mapping(value, key_name):
            return True
        if not is_call(value, "items") or not isinstance(value.func, ast.Attribute):
            return False
        items_source = value.func.value
        if dict_has_launch_config_mapping(items_source, key_name):
            return True
        return any(name_loads(items_source, name) for name in assigned_dicts)

    for node in ast.walk(tree):
        if not is_call(node, "IncludeLaunchDescription"):
            continue
        for keyword in node.keywords:
            if keyword.arg == "launch_arguments" and forwards_launch_config_mapping(
                keyword.value
            ):
                return True
    return False


def python_uses_absolute_world_check(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "startswith" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and first_arg.value == "/":
                    return True
            if node.func.attr in {"is_absolute", "isabs"}:
                return True
        elif isinstance(node.func, ast.Name) and node.func.id == "isabs":
            return True
    return False


def parse_model_config(model_dir):
    return parse_xml(model_dir / "model.config")


def parse_model_sdf(model_dir):
    return parse_xml(model_dir / "model.sdf")


def parse_world(world_path):
    return parse_xml(world_path)


def include_effective_name(include):
    explicit_name = include.findtext("name", default="").strip()
    if explicit_name:
        return explicit_name

    uri = include.findtext("uri", default="").strip()
    if uri.startswith("model://"):
        return uri.removeprefix("model://").rstrip("/").split("/")[-1]
    return None


def test_expected_gazebo_models_are_fuel_compatible():
    for model_name in EXPECTED_MODELS:
        model_dir = MODELS / model_name
        assert model_dir.is_dir(), f"missing model directory: {model_name}"
        assert (model_dir / "model.config").is_file(), f"missing model.config: {model_name}"
        assert (model_dir / "model.sdf").is_file(), f"missing model.sdf: {model_name}"

        config = parse_model_config(model_dir)
        sdf = parse_model_sdf(model_dir)
        model = sdf.find("model")
        static = model.find("static") if model is not None else None

        assert config.findtext("name") == model_name
        assert sdf.tag == "sdf"
        assert sdf.attrib.get("version") == "1.11"
        assert model is not None
        assert model.attrib.get("name") == model_name
        assert static is not None
        assert static.text.strip() == "true"


def test_expected_scenario_worlds_exist_and_include_reusable_models():
    for world_file in EXPECTED_WORLDS:
        path = WORLDS / world_file
        assert path.is_file(), f"missing world: {world_file}"
        sdf = parse_world(path)
        plugin_filenames = {plugin.attrib.get("filename") for plugin in sdf.findall(".//plugin")}
        include_uris = {include.findtext("uri") for include in sdf.findall(".//include")}

        assert sdf.tag == "sdf"
        assert sdf.attrib.get("version") == "1.11"
        assert "gz-sim-physics-system" in plugin_filenames
        assert "gz-sim-sensors-system" in plugin_filenames
        assert "gz-sim-scene-broadcaster-system" in plugin_filenames
        assert "model://warehouse_shelf" in include_uris
        assert "model://warehouse_pallet" in include_uris


def test_world_model_includes_reference_existing_models():
    model_names = {path.name for path in MODELS.iterdir() if path.is_dir()}

    for world in WORLDS.glob("*.sdf"):
        root = parse_world(world)
        for include in root.findall(".//include"):
            uri = include.findtext("uri", default="").strip()
            if uri.startswith("model://"):
                model_name = uri.removeprefix("model://")
                assert model_name in model_names, f"{world.name} references missing model {model_name}"


def test_world_includes_have_unique_effective_model_names():
    for world in WORLDS.glob("*.sdf"):
        root = parse_world(world)
        names = [
            name
            for include in root.findall(".//include")
            if (name := include_effective_name(include)) is not None
        ]
        duplicate_names = sorted(
            name for name, count in Counter(names).items() if count > 1
        )

        assert not duplicate_names, f"{world.name} has duplicate include names: {duplicate_names}"


def test_world_poses_use_six_value_euler_rpy_format():
    for world in WORLDS.glob("*.sdf"):
        root = parse_world(world)
        for pose in root.findall(".//pose"):
            values = pose.text.strip().split() if pose.text else []
            assert len(values) == 6, f"{world.name} has malformed pose: {pose.text!r}"


def test_gazebo_launch_accepts_external_worlds_and_extra_resource_path():
    text = read(GAZEBO_LAUNCH)
    tree = parse_python(GAZEBO_LAUNCH)
    constants = string_constants(tree)
    calls = called_names(tree)

    assert "extra_gz_resource_path" in constants
    assert "GZ_SIM_RESOURCE_PATH" in constants
    assert "models" in constants
    assert "SetEnvironmentVariable" in calls or "SetEnvironmentVariable" in text
    assert python_uses_absolute_world_check(tree)


def test_bringup_forwards_extra_gz_resource_path():
    tree = parse_python(BRINGUP_LAUNCH)
    constants = string_constants(tree)
    calls = called_names(tree)

    assert "extra_gz_resource_path" in constants
    assert "DeclareLaunchArgument" in calls
    assert include_launch_forwards_arg(tree, "extra_gz_resource_path")
