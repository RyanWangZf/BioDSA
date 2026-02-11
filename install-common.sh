#!/bin/bash
#
# Shared functions for BioDSA Skills install scripts
#
# Installs BOTH skill sets:
#   - biodsa-agent-development  (from biodsa-agent-dev-skills/)
#   - biodsa-agent-execution    (from biodsa-agent-exec-skills/)
#
# Sourced by install-cursor.sh, install-claude-code.sh, install-codex.sh,
# install-gemini.sh, install-openclaw.sh
#
# Each installer must define before calling run_installer:
#   TOOL_NAME             - Display name (e.g., "Cursor", "Claude Code")
#   INSTALL_MODE          - "project" or "global"
#   DEFAULT_SKILLS_BASE   - Global install base (e.g., "$HOME/.claude/skills")
#   PROJECT_SKILLS_BASE   - Project-level subdirectory (e.g., ".cursor/skills")
#   print_usage()         - Tool-specific help text

set -e

# Resolve paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"

# ── Skill Set Definitions ────────────────────────────────────
# Each skill set: (source_directory, install_folder_name)
SKILL_SOURCES=(
    "$SCRIPT_DIR/biodsa-agent-dev-skills"
    "$SCRIPT_DIR/biodsa-agent-exec-skills"
)
SKILL_INSTALL_NAMES=(
    "biodsa-agent-development"
    "biodsa-agent-execution"
)

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ── Defaults ──────────────────────────────────────────────────
PROJECT_PATH=""
UNINSTALL_MODE=false
DRY_RUN=false
VERBOSE=false

# ── Helper Functions ──────────────────────────────────────────

print_common_options() {
    echo "  --project [PATH]   Install to a specific project directory (default: current directory)"
    echo "  --uninstall        Remove installed skills from the target location"
    echo "  --dry-run          Preview what would be installed without making changes"
    echo "  --verbose          Show detailed output"
    echo "  --help             Show this help message"
}

validate_source() {
    local errors=0
    for i in "${!SKILL_SOURCES[@]}"; do
        local src="${SKILL_SOURCES[$i]}"
        local name="${SKILL_INSTALL_NAMES[$i]}"
        if [ ! -d "$src" ]; then
            echo -e "  ${RED}Missing source directory: $src${NC}"
            errors=$((errors + 1))
            continue
        fi
        local count
        count=$(find "$src" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -eq 0 ]; then
            echo -e "  ${RED}No .md files found in $src${NC}"
            errors=$((errors + 1))
        elif [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}Found${NC} $count files for $name"
        fi
    done
    if [ $errors -gt 0 ]; then
        echo -e "${RED}Error: $errors skill set(s) have issues. Aborting.${NC}"
        exit 1
    fi
}

do_uninstall() {
    local base_dir="$1"
    local removed=0

    for name in "${SKILL_INSTALL_NAMES[@]}"; do
        local target="$base_dir/$name"
        if [ -d "$target" ]; then
            echo "Removing: $target"
            rm -rf "$target"
            removed=$((removed + 1))
        fi
    done

    if [ $removed -eq 0 ]; then
        echo "No BioDSA skills found at: $base_dir"
    else
        echo -e "${GREEN}Uninstalled $removed skill set(s).${NC}"
    fi

    # Clean up empty parent directories
    if [ -d "$base_dir" ] && [ -z "$(ls -A "$base_dir" 2>/dev/null)" ]; then
        rmdir "$base_dir" 2>/dev/null && echo "Removed empty skills directory."
    fi
    exit 0
}

do_dry_run() {
    local base_dir="$1"

    echo "Dry run — would install to: $base_dir/"
    echo ""

    local total=0
    for i in "${!SKILL_SOURCES[@]}"; do
        local src="${SKILL_SOURCES[$i]}"
        local name="${SKILL_INSTALL_NAMES[$i]}"
        echo "  $name/"
        for f in "$src"/*.md; do
            local fname
            fname=$(basename "$f")
            local fsize
            fsize=$(wc -c < "$f" | tr -d ' ')
            echo "    $fname ($fsize bytes)"
            total=$((total + 1))
        done
        echo ""
    done

    echo "Total: $total files across ${#SKILL_SOURCES[@]} skill sets"
    echo ""
    echo -e "${YELLOW}No changes made (dry run).${NC}"
    exit 0
}

do_install() {
    local base_dir="$1"

    echo ""
    echo -e "${BLUE}BioDSA Skills — $TOOL_NAME Installer${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    validate_source

    if [ "$DRY_RUN" = true ]; then
        do_dry_run "$base_dir"
    fi

    echo "Installing to: $base_dir/"
    echo ""

    local total_installed=0

    for i in "${!SKILL_SOURCES[@]}"; do
        local src="${SKILL_SOURCES[$i]}"
        local name="${SKILL_INSTALL_NAMES[$i]}"
        local target="$base_dir/$name"

        mkdir -p "$target"

        local count=0
        for f in "$src"/*.md; do
            local fname
            fname=$(basename "$f")
            cp "$f" "$target/$fname"
            count=$((count + 1))
            if [ "$VERBOSE" = true ]; then
                echo -e "  ${GREEN}✓${NC} $name/$fname"
            fi
        done

        echo -e "  ${GREEN}$name${NC} — $count files"
        total_installed=$((total_installed + count))
    done

    echo ""
    echo -e "${GREEN}Installation complete.${NC} ($total_installed files across ${#SKILL_SOURCES[@]} skill sets)"
    echo ""
}

print_try_message() {
    echo -e "${BLUE}Example prompts to try:${NC}"
    echo ""
    echo -e "  ${GREEN}Set up the environment${NC}"
    echo '    "Set up the BioDSA environment for me — conda, pipenv, .env, everything"'
    echo ""
    echo -e "  ${GREEN}Run an existing agent on a task${NC}"
    echo '    "Use DeepEvidenceAgent to find what resistance mechanisms exist for'
    echo '     EGFR inhibitors in lung cancer — save results as PDF"'
    echo '    "I have a patient note — run TrialGPTAgent to find matching clinical trials"'
    echo '    "Analyze my cBioPortal breast cancer dataset with DSWizardAgent —'
    echo '     find survival differences between TP53 mutant and wild-type groups"'
    echo '    "Run a systematic literature review on GLP-1 agonists for weight loss'
    echo '     in type 2 diabetes with SLRMetaAgent and produce forest plots"'
    echo ""
    echo -e "  ${GREEN}Create a new agent${NC}"
    echo '    "Build an agent that searches PubMed, ChEMBL, and Open Targets to find'
    echo '     drug repurposing opportunities for rare diseases"'
    echo '    "Here is a paper on clinical evidence synthesis — implement it as a'
    echo '     BioDSA multi-agent system"'
    echo ""
    echo -e "  ${GREEN}Evaluate on benchmarks${NC}"
    echo '    "Batch-evaluate the ReactAgent on benchmarks/HLE-medicine/ and report accuracy"'
    echo '    "Build a literature QA agent and test it on the LabBench benchmark"'
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

    # Determine base directory for skills
    if [ "$INSTALL_MODE" = "project" ]; then
        if [ -n "$PROJECT_PATH" ]; then
            SKILLS_BASE="$PROJECT_PATH/$PROJECT_SKILLS_BASE"
        else
            SKILLS_BASE="$(pwd)/$PROJECT_SKILLS_BASE"
        fi
    else
        SKILLS_BASE="$DEFAULT_SKILLS_BASE"
    fi

    # Uninstall
    if [ "$UNINSTALL_MODE" = true ]; then
        do_uninstall "$SKILLS_BASE"
    fi

    # Install
    do_install "$SKILLS_BASE"
}
