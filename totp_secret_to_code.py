#!/usr/bin/env python3
import sys
import pyotp

if __name__ == "__main__":
    # Check if the secret was provided as a command-line argument
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <TOTP secret>")
        sys.exit(1)

    # Retrieve the secret from the arguments
    secret = sys.argv[1]

    # Create a TOTP object using the provided secret
    totp = pyotp.TOTP(secret)

    # Print the current TOTP code
    print("TOTP Code:", totp.now())
