#!/bin/bash

set -e

echo "🔍 Checking dependency version consistency..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_PYPROJECT="$ROOT_DIR/pyproject.toml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if we found any issues
ISSUES_FOUND=false

# Function to extract version from pyproject.toml
get_version() {
    local file="$1"
    grep '^version = ' "$file" | sed 's/version = "\(.*\)"/\1/'
}

# Function to extract dependency version from pyproject.toml
get_dependency_version() {
    local file="$1"
    local dep_name="$2"
    grep "\"$dep_name>=" "$file" | sed 's/.*"'$dep_name'>=\([^"]*\)".*/\1/' | head -n1
}

echo "📋 Main package version:"
MAIN_VERSION=$(get_version "$MAIN_PYPROJECT")
echo "  hammad-python: $MAIN_VERSION"

echo ""
echo "📋 Library package versions:"

# Build list of lib packages and versions using temp files instead of associative arrays
LIB_LIST_FILE=$(mktemp)
trap "rm -f $LIB_LIST_FILE" EXIT

for lib_dir in "$ROOT_DIR"/libs/*/; do
    if [[ -d "$lib_dir" && -f "$lib_dir/pyproject.toml" ]]; then
        package_name=$(basename "$lib_dir")
        version=$(get_version "$lib_dir/pyproject.toml")
        echo "$package_name $version" >> "$LIB_LIST_FILE"
        echo "  $package_name: $version"
    fi
done

# Function to get lib version by name
get_lib_version() {
    local lib_name="$1"
    grep "^$lib_name " "$LIB_LIST_FILE" | cut -d' ' -f2
}

echo ""
echo "🔍 Checking version consistency..."

# Check if main package dependencies match lib package versions
echo ""
echo "Main package dependencies vs actual lib versions:"
while read -r lib_name actual_version; do
    required_version=$(get_dependency_version "$MAIN_PYPROJECT" "$lib_name")
    
    if [[ -n "$required_version" ]]; then
        if [[ "$required_version" == "$actual_version" ]]; then
            echo -e "  ✅ $lib_name: required $required_version, actual $actual_version ${GREEN}(match)${NC}"
        else
            echo -e "  ❌ $lib_name: required $required_version, actual $actual_version ${RED}(mismatch)${NC}"
            ISSUES_FOUND=true
        fi
    else
        echo -e "  ⚠️  $lib_name: ${YELLOW}not found in main dependencies${NC}"
        ISSUES_FOUND=true
    fi
done < "$LIB_LIST_FILE"

echo ""
echo "Cross-library dependencies:"

# Check cross-dependencies between lib packages
for lib_dir in "$ROOT_DIR"/libs/*/; do
    if [[ -d "$lib_dir" && -f "$lib_dir/pyproject.toml" ]]; then
        package_name=$(basename "$lib_dir")
        echo ""
        echo "  $package_name dependencies:"
        
        # Check each dependency in this lib
        while read -r dep_lib_name dep_actual_version; do
            if [[ "$dep_lib_name" != "$package_name" ]]; then
                required_version=$(get_dependency_version "$lib_dir/pyproject.toml" "$dep_lib_name")
                if [[ -n "$required_version" ]]; then
                    if [[ "$required_version" == "$dep_actual_version" ]]; then
                        echo -e "    ✅ $dep_lib_name: required $required_version, actual $dep_actual_version ${GREEN}(match)${NC}"
                    else
                        echo -e "    ❌ $dep_lib_name: required $required_version, actual $dep_actual_version ${RED}(mismatch)${NC}"
                        ISSUES_FOUND=true
                    fi
                fi
            fi
        done < "$LIB_LIST_FILE"
    fi
done

echo ""
if [[ "$ISSUES_FOUND" == "true" ]]; then
    echo -e "${RED}❌ Version inconsistencies found! Please update version numbers to match.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All dependency versions are consistent!${NC}"
    exit 0
fi