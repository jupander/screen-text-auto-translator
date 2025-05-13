import argostranslate.package
#import argostranslate.translate

# Define source and target languages
from_code = "fr"
to_code = "en"

# Update the package index to get the latest available models
argostranslate.package.update_package_index()

# Retrieve the list of available packages
available_packages = argostranslate.package.get_available_packages()

# Find the package that matches the desired language pair
package_to_install = next(
    (pkg for pkg in available_packages if pkg.from_code == from_code and pkg.to_code == to_code),
    None
)

if package_to_install:
    # Download and install the package
    download_path = package_to_install.download()
    argostranslate.package.install_from_path(download_path)
    print(f"Successfully installed the {from_code} to {to_code} translation model.")
else:
    print(f"No translation package found for {from_code} to {to_code}.")
