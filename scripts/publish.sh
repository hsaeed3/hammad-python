#!/bin/bash

set -e

echo "🚀 Publishing updated packages..."

# Function to check if package has changes since last git tag
has_changes() {
    local package_dir="$1"
    local package_name="$2"
    
    # Get the last tag for this package (if any)
    local last_tag=$(git tag -l "${package_name}-*" --sort=-version:refname | head -n1)
    
    if [[ -z "$last_tag" ]]; then
        echo "No previous tag found for $package_name, treating as changed"
        return 0
    fi
    
    # Check if there are changes since the last tag in the package directory
    local changes=$(git diff --name-only "$last_tag"..HEAD -- "$package_dir")
    
    if [[ -n "$changes" ]]; then
        echo "Changes detected in $package_name since $last_tag"
        return 0
    else
        echo "No changes in $package_name since $last_tag"
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
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check main package
echo "🔍 Checking main package..."
if has_changes "$ROOT_DIR" "hammad-python"; then
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
        
        if has_changes "$lib_dir" "$package_name"; then
            echo "📦 Publishing $package_name..."
            publish_package "$lib_dir" "$package_name" "true"
        else
            echo "⏭️  Skipping $package_name (no changes)"
        fi
    fi
done

echo "🎉 Publishing complete!"