#!/bin/bash
#
# Install BioDSA Agent Development Skills to Gemini CLI
#
# Usage:
#   ./install-gemini.sh                            # Install globally (~/.gemini/skills/)
#   ./install-gemini.sh --project                  # Install to current project
#   ./install-gemini.sh --project /path/to/project # Install to specific project
#   ./install-gemini.sh --uninstall                # Remove installed skills
#   ./install-gemini.sh --dry-run                  # Preview what would be installed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

TOOL_NAME="Gemini CLI"
INSTALL_MODE="global"
DEFAULT_TARGET_DIR="$HOME/.gemini/skills/$SKILL_NAME"
PROJECT_SUBDIR=".gemini/skills/$SKILL_NAME"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install BioDSA Agent Development Skills to Gemini CLI"
    echo ""
    echo "Options:"
    echo "  --global           Install to global Gemini skills (~/.gemini/skills/) [default]"
    echo "  --project [PATH]   Install to a project directory (default: current directory)"
    echo "  --uninstall        Remove installed skills from the target location"
    echo "  --dry-run          Preview what would be installed without making changes"
    echo "  --verbose          Show detailed output"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Install globally"
    echo "  $0 --project                          # Install to current project"
    echo "  $0 --project ~/my-project             # Install to ~/my-project"
    echo "  $0 --uninstall                        # Remove global install"
    echo "  $0 --project ~/my-project --uninstall # Remove from project"
}

run_installer "$@"

if [ "$INSTALL_MODE" = "global" ]; then
    echo "Skills installed globally. They will be available in all Gemini CLI sessions."
else
    echo "Skills installed to project. They will be available when working in this project."
fi
echo ""
print_try_message
