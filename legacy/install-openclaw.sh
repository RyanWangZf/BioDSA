#!/bin/bash
#
# Install BioDSA Skills to OpenClaw
#
# Installs both skill sets:
#   - Agent Development Skills (for creating new agents)
#   - Agent Execution Skills  (for running existing agents)
#
# Usage:
#   ./install-openclaw.sh                            # Install globally (~/.openclaw/skills/)
#   ./install-openclaw.sh --project                  # Install to current project
#   ./install-openclaw.sh --project /path/to/project # Install to specific project/workspace
#   ./install-openclaw.sh --uninstall                # Remove installed skills
#   ./install-openclaw.sh --dry-run                  # Preview what would be installed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

TOOL_NAME="OpenClaw"
INSTALL_MODE="global"
DEFAULT_SKILLS_BASE="$HOME/.openclaw/skills"
PROJECT_SKILLS_BASE="skills"

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install BioDSA Skills to OpenClaw"
    echo ""
    echo "Options:"
    echo "  --global           Install to global OpenClaw skills (~/.openclaw/skills/) [default]"
    echo "  --project [PATH]   Install to a project/workspace directory (default: current directory)"
    echo "  --uninstall        Remove installed skills from the target location"
    echo "  --dry-run          Preview what would be installed without making changes"
    echo "  --verbose          Show detailed output"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Install globally"
    echo "  $0 --project                          # Install to current project"
    echo "  $0 --project ~/my-workspace           # Install to ~/my-workspace"
    echo "  $0 --uninstall                        # Remove global install"
    echo "  $0 --project ~/my-workspace --uninstall # Remove from workspace"
}

run_installer "$@"

if [ "$INSTALL_MODE" = "global" ]; then
    echo "Skills installed globally. Start a new OpenClaw session for skills to take effect."
else
    echo "Skills installed to workspace. They will be available when working in this project."
fi
echo ""
print_try_message
