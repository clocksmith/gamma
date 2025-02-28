import os

output_filename = "cat.txt"

with open(output_filename, "w", encoding="utf-8") as outfile:
    for filename in os.listdir("."):
        if (
            os.path.isfile(filename)
            and filename != output_filename
            and filename != "LICENSE"
            and filename != "codecat.py"
        ):
            try:
                with open(filename, "r", encoding="utf-8") as infile:
                    outfile.write(f"# --- {filename} ---\n")
                    outfile.write(infile.read())
                    outfile.write("\n\n")
            except Exception as e:
                error_message = f"Error type: {type(e).__name__}, Error: {e}"
                print(f"Error reading file: {filename} - {error_message}")
                outfile.write(f"--- ERROR READING FILE: {filename} ---\n")
                outfile.write(f"{error_message}\n\n")

print(f"Code cat complete. See '{output_filename}'")
