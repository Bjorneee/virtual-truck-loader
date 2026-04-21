import argparse
from app.viewer import SimpleSceneViewer


def main():
    parser = argparse.ArgumentParser(description="VTL Panda3D Viewer")
    parser.add_argument(
        "input_json",
        type=str,
        help="Path to input JSON payload for packing"
    )

    args = parser.parse_args()

    app = SimpleSceneViewer(input_json_path=args.input_json)
    app.run()


if __name__ == "__main__":
    main()