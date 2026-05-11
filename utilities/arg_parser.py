import argparse

# 1. Create the parser
parser = argparse.ArgumentParser(description="A script to greet the user.")

# 2. Add arguments
parser.add_argument("-n", "--name", type=str, help="User name", required=True)

# 3. Parse arguments
args = parser.parse_args()

# 4. Use arguments
print(f"Hello, {args.name}")
