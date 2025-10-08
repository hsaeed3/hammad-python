#!/bin/bash

set -e

echo "🚀 Publishing updated packages..."

# Function to get current version from pyproject.toml
get_local_version() {
    local package_dir="$1"
    local pyproject_file="$package_dir/pyproject.toml"
    
    if [[ ! -f "$pyproject_file" ]]; then
        echo ""
        return
    fi
    
    # Extract version from pyproject.toml using awk for more reliable parsing
    awk -F'"' '/^version[[:space:]]*=/ {print $2}' "$pyproject_file" | head -n1
}

# Function to get latest version from PyPI
get_pypi_version() {
    local package_name="$1"
    
    # Query PyPI API for package info
    local response=$(curl -s "https://pypi.org/pypi/$package_name/json" 2>/dev/null || echo "{}")
    
    # Extract version using Python for reliable JSON parsing
    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('info', {}).get('version', ''))
except:
    print('')
"
}

# Function to check if package needs publishing based on PyPI version
needs_publishing() {
    local package_dir="$1"
    local package_name="$2"
    
    # Get local version
    local local_version=$(get_local_version "$package_dir")
    
    if [[ -z "$local_version" ]]; then
        echo "❌ Could not determine local version for $package_name"
        return 1
    fi
    
    echo "📌 Local version of $package_name: $local_version"
    
    # Get PyPI version
    local pypi_version=$(get_pypi_version "$package_name")
    
    if [[ -z "$pypi_version" ]]; then
        echo "📤 Package $package_name not found on PyPI, needs publishing"
        return 0
    fi
    
    echo "🌐 PyPI version of $package_name: $pypi_version"
    
    # Compare versions
    if [[ "$local_version" != "$pypi_version" ]]; then
        echo "✅ Version mismatch detected, needs publishing ($pypi_version → $local_version)"
        return 0
    else
        echo "⏭️  Versions match, skipping"
        return 1
    fi
}

# Function to build and upload a package
publish_package() {
    local package_dir="$1"
    local package_name="$2"
    local is_workspace_member="$3"
    
    echo "📦 Building $package_name..."
    
    if [[ "$is_workspace_member" == "true" ]]; then
        # For workspace members, build from root and look for files in root dist
        cd "$ROOT_DIR"
        
        # Clean previous builds for this package from root dist
        rm -rf dist/${package_name//-/_}-* dist/${package_name}-*
        
        # Build the specific package
        uv build --package "$package_name"
        
        # Look for built files in root dist directory
        local built_files=$(find dist/ -name "${package_name//-/_}-*" -o -name "${package_name}-*" 2>/dev/null || true)
        
        if [[ -z "$built_files" ]]; then
            echo "❌ Build failed for $package_name - no built files found in dist/"
            return 1
        fi
        
        # Upload to PyPI
        echo "📤 Uploading $package_name to PyPI..."
        twine upload $built_files
        
    else
        # For standalone packages, build in their own directory
        cd "$package_dir"
        
        # Clean previous builds
        rm -rf dist/ build/ *.egg-info/
        
        # Build the package
        uv build
        
        if [[ ! -d "dist" ]]; then
            echo "❌ Build failed for $package_name - no dist directory created"
            return 1
        fi
        
        # Upload to PyPI
        echo "📤 Uploading $package_name to PyPI..."
        twine upload dist/*
        
        # Return to root directory
        cd - > /dev/null
    fi
    
    echo "✅ Successfully published $package_name"
    return 0
}

# Get the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check main package
echo "🔍 Checking main package..."
if needs_publishing "$ROOT_DIR" "hammad-python"; then
    echo "📦 Publishing main package (hammad-python)..."
    publish_package "$ROOT_DIR" "hammad-python" "false"
else
    echo "⏭️  Skipping main package (no changes)"
fi

# Check each lib package
echo "🔍 Checking lib packages..."
for lib_dir in "$ROOT_DIR"/libs/*/; do
    if [[ -d "$lib_dir" && -f "$lib_dir/pyproject.toml" ]]; then
        package_name=$(basename "$lib_dir")
        echo "🔍 Checking $package_name..."
        
        if needs_publishing "$lib_dir" "$package_name"; then
            echo "📦 Publishing $package_name..."
            publish_package "$lib_dir" "$package_name" "true"
        else
            echo "⏭️  Skipping $package_name (no changes)"
        fi
    fi
done

echo "🎉 Publishing complete!"