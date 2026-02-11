#!/bin/bash
#
# Install BioDSA Agent Development Skills to Cursor IDE
#
# Usage:
#   ./install-cursor.sh                            # Install to current project
#   ./install-cursor.sh --project /path/to/project  # Install to specific project
#   ./install-cursor.sh --uninstall                 # Remove installed skills
#   ./install-cursor.sh --dry-run                   # Preview what would be installed
#
# Cursor skills are always project-level (in .cursor/skills/)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

TOOL_NAME="Cursor"
INSTALL_MODE="project"
DEFAULT_TARGET_DIR="$(pwd)/.cursor/skills/$SKILL_NAME"
PROJECT_SUBDIR=".cursor/skills/$SKILL_NAME"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install BioDSA Agent Development Skills to Cursor IDE"
    echo ""
    echo "Options:"
    echo "  --project [PATH]   Install to a specific project directory (default: current directory)"
    echo "  --uninstall        Remove installed skills from the target project"
    echo "  --dry-run          Preview what would be installed without making changes"
    echo "  --verbose          Show detailed output"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Install to current project"
    echo "  $0 --project ~/my-project             # Install to ~/my-project"
    echo "  $0 --project ~/my-project --uninstall # Remove from ~/my-project"
}

run_installer "$@"

echo "The skills are now available in Cursor. When you ask Cursor to help you"
echo "create a new BioDSA agent, it will automatically read these skills."
echo ""
print_try_message
