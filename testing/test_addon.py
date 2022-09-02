import os
import sys
try:
    import blender_addon_tester as BAT
except Exception as e:
    print(e)
    sys.exit(1)


def main():
    if len(sys.argv) > 1:
        addon = sys.argv[1]
    else:
        addon = "ActRec"
    if len(sys.argv) > 2:
        blender_rev = sys.argv[2]
    else:
        blender_rev = "2.93"  # LTS

    if len(sys.argv) > 3:
        test_format = sys.argv[3]
    else:
        test_format = "unit"

    config = {
        "coverage": True,
        "tests": os.path.join("testing", test_format),
        "pytest_args": "--tb=long"
    }

    try:
        exit_val = BAT.test_blender_addon(addon_path=addon, blender_revision=blender_rev, config=config)
    except Exception as e:
        print(e)
        exit_val = 1
    sys.exit(exit_val)


if __name__ == "__main__":
    main()
