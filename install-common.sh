#!/bin/bash
#
# Shared functions for BioDSA Agent Development Skills install scripts
#
# Sourced by install-cursor.sh, install-claude-code.sh, install-codex.sh,
# install-gemini.sh, install-openclaw.sh
#
# Each installer must define before calling run_installer:
#   TOOL_NAME          - Display name (e.g., "Cursor", "Claude Code")
#   INSTALL_MODE       - "project" (project-only tools) or "global" (default for others)
#   DEFAULT_TARGET_DIR - Global install path (e.g., "$HOME/.claude/skills/$SKILL_NAME")
#   PROJECT_SUBDIR     - Project-level subdirectory (e.g., ".claude/skills/$SKILL_NAME")
#   print_usage()      - Tool-specific help text

set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
SKILL_SOURCE_DIR="$SCRIPT_DIR/biodsa-agent-dev-skills"
SKILL_NAME="biodsa-agent-development"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults (can be overridden by tool scripts before calling run_installer)
PROJECT_PATH=""
UNINSTALL_MODE=false
DRY_RUN=false
VERBOSE=false

# List of skill files to install
SKILL_FILES=(
    "SKILL.md"
    "01-base-agent.md"
    "02-single-agent.md"
    "03-multi-agent.md"
    "04-tools-and-wrappers.md"
    "05-deliverables-and-testing.md"
    "06-user-workflows.md"
)

print_common_options() {
    echo "  --project [PATH]   Install to a specific project directory (default: current directory)"
    echo "  --uninstall        Remove installed skills from the target location"
    echo "  --dry-run          Preview what would be installed without making changes"
    echo "  --verbose          Show detailed output"
    echo "  --help             Show this help message"
}

validate_source() {
    local missing=0
    for f in "${SKILL_FILES[@]}"; do
        if [ ! -f "$SKILL_SOURCE_DIR/$f" ]; then
            echo -e "  ${RED}Missing source file: $f${NC}"
            missing=$((missing + 1))
        fi
    done
    if [ $missing -gt 0 ]; then
        echo -e "${RED}Error: $missing source file(s) missing from $SKILL_SOURCE_DIR. Aborting.${NC}"
        exit 1
    fi
}

do_uninstall() {
    local target_dir="$1"
    if [ ! -d "$target_dir" ]; then
        echo "No skills found at: $target_dir"
        exit 0
    fi
    echo "Removing BioDSA skills from: $target_dir"
    rm -rf "$target_dir"
    echo -e "${GREEN}Uninstall complete.${NC}"

    # Clean up empty parent directories
    local parent_dir
    parent_dir="$(dirname "$target_dir")"
    if [ -d "$parent_dir" ] && [ -z "$(ls -A "$parent_dir" 2>/dev/null)" ]; then
        rmdir "$parent_dir" 2>/dev/null && echo "Removed empty skills directory."
    fi
    exit 0
}

do_dry_run() {
    local target_dir="$1"
    echo "Dry run — would install to: $target_dir"
    echo ""
    echo "Would install ${#SKILL_FILES[@]} files:"
    for f in "${SKILL_FILES[@]}"; do
        local_size=$(wc -c < "$SKILL_SOURCE_DIR/$f" | tr -d ' ')
        echo "  $f ($local_size bytes)"
    done
    echo ""
    echo -e "${YELLOW}No changes made (dry run).${NC}"
    exit 0
}

do_install() {
    local target_dir="$1"

    echo ""
    echo -e "${BLUE}BioDSA Agent Development Skills — $TOOL_NAME Installer${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    validate_source

    if [ "$DRY_RUN" = true ]; then
        do_dry_run "$target_dir"
    fi

    echo "Installing to: $target_dir"
    echo ""

    # Create target directory
    mkdir -p "$target_dir"

    # Copy files
    local installed=0
    for f in "${SKILL_FILES[@]}"; do
        cp "$SKILL_SOURCE_DIR/$f" "$target_dir/$f"
        installed=$((installed + 1))
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}Installed${NC}: $f"
        fi
    done

    echo -e "  Installed ${GREEN}$installed${NC} files"
    echo ""
    echo -e "${GREEN}Installation complete.${NC}"
    echo ""
}

print_try_message() {
    echo "Try asking:"
    echo '  "Create a new agent called DrugDiscovery that searches PubMed and ChEMBL"'
    echo '  "Build an agent and evaluate it on benchmarks/HLE-medicine/"'
    echo '  "Here is a paper — implement it as a BioDSA agent"'
    echo ""
}

run_installer() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --global)
                INSTALL_MODE="global"
                shift
                ;;
            --project)
                INSTALL_MODE="project"
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    PROJECT_PATH="$2"
                    shift
                fi
                shift
                ;;
            --uninstall)
                UNINSTALL_MODE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                print_usage
                exit 1
                ;;
        esac
    done

    # Determine target directory
    if [ "$INSTALL_MODE" = "project" ]; then
        if [ -n "$PROJECT_PATH" ]; then
            TARGET_DIR="$PROJECT_PATH/$PROJECT_SUBDIR"
        else
            TARGET_DIR="$(pwd)/$PROJECT_SUBDIR"
        fi
    else
        TARGET_DIR="$DEFAULT_TARGET_DIR"
    fi

    # Uninstall
    if [ "$UNINSTALL_MODE" = true ]; then
        do_uninstall "$TARGET_DIR"
    fi

    # Install
    do_install "$TARGET_DIR"
}
