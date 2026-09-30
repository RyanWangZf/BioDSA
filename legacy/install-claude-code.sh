#!/bin/bash
#
# Install BioDSA Skills to Claude Code
#
# Installs both skill sets:
#   - Agent Development Skills (for creating new agents)
#   - Agent Execution Skills  (for running existing agents)
#
# Usage:
#   ./install-claude-code.sh                            # Install globally (~/.claude/skills/)
#   ./install-claude-code.sh --project                  # Install to current project
#   ./install-claude-code.sh --project /path/to/project # Install to specific project
#   ./install-claude-code.sh --uninstall                # Remove installed skills
#   ./install-claude-code.sh --dry-run                  # Preview what would be installed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

TOOL_NAME="Claude Code"
INSTALL_MODE="global"
DEFAULT_SKILLS_BASE="$HOME/.claude/skills"
PROJECT_SKILLS_BASE=".claude/skills"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install BioDSA Skills to Claude Code"
    echo ""
    echo "Options:"
    echo "  --global           Install to global Claude skills (~/.claude/skills/) [default]"
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
    echo "Skills installed globally. They will be available in all Claude Code sessions."
else
    echo "Skills installed to project. They will be available when working in this project."
fi
echo ""
print_try_message
