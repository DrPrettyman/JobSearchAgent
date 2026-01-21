# JobSearch GUI Project

This document tracks the GUI implementation for the JobSearch application.

## Overview

The GUI provides an alternative interface to the existing CLI, using **PySide6** (Qt for Python). Both interfaces share the same business logic and data layer.

## Architecture

```
src/
├── main.py                    # Main entry point (supports --gui flag)
├── gui_main.py                # Standalone GUI entry point
├── gui/
│   ├── __init__.py
│   ├── app.py                 # QApplication setup, theming
│   ├── main_window.py         # Main window with sidebar navigation
│   ├── workers.py             # QThread workers for async operations
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py       # Overview, stats, quick actions
│   │   ├── profile.py         # User info editing
│   │   ├── search.py          # Search config & execution
│   │   ├── jobs_list.py       # Job browser with filters
│   │   └── job_detail.py      # Single job view + actions
│   │
│   └── widgets/
│       ├── __init__.py
│       ├── job_card.py        # Compact job display widget
│       ├── status_badge.py    # Status indicator badges
│       └── collapsible.py     # Collapsible section widget
│
├── services/                  # Shared (no changes needed)
├── data_handlers/             # Shared (no changes needed)
└── ...
```

## Shared Components (No Changes Needed)

These components are already UI-agnostic and will be reused:

| Component | Purpose |
|-----------|---------|
| `data_handlers/` | User, Job, Query models with SQLite persistence |
| `services/` | CoverLetterService, UserProfileService |
| `search_jobs.py` | JobSearcher class |
| `utils.py` | Document parsing, Claude API calls |
| `cover_letter_writer.py` | LaTeX/PDF generation |
| `online_presence.py` | LinkedIn/GitHub scraping |
| `question_answerer.py` | Application question answering |

## Pages & Features

### 1. Dashboard (`dashboard.py`)
- Welcome message with user name
- Job statistics cards (pending, in progress, applied, discarded)
- Quick action buttons
- Recent activity summary

### 2. Jobs List (`jobs_list.py`)
- Tab bar or filter buttons for job status
- Scrollable list of job cards
- Click to open job detail
- Batch actions (future)

### 3. Job Detail (`job_detail.py`)
- Job information display
- Status badge with transition buttons
- Cover letter section (generate, view, export PDF)
- Application questions section
- Edit job details dialog
- Writing style customization

### 4. Profile (`profile.py`)
- Form-based editing of user info
- Source documents management (add/remove files)
- Online presence configuration
- Summary generation button
- Job titles/locations management

### 5. Search (`search.py`)
- Search criteria display
- Query management (generate, review, remove)
- Search execution with progress
- Results display

## Threading Strategy

Long-running operations must run in background threads:

```python
class Worker(QThread):
    finished = Signal(object)
    progress = Signal(str, str)  # message, level

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        # Pass progress callback to service
        self.kwargs['on_progress'] = lambda msg, lvl: self.progress.emit(msg, lvl)
        result = self.fn(*self.args, **self.kwargs)
        self.finished.emit(result)
```

Operations requiring threading:
- Job search
- Cover letter generation
- PDF export
- Online presence refresh
- Comprehensive summary generation
- Search query generation

## Color Scheme

Using a professional, accessible color scheme:

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Primary | #2563eb (blue) | #3b82f6 |
| Success | #16a34a (green) | #22c55e |
| Warning | #ca8a04 (yellow) | #eab308 |
| Error | #dc2626 (red) | #ef4444 |
| Background | #ffffff | #1e1e1e |
| Surface | #f3f4f6 | #2d2d2d |
| Text | #1f2937 | #f3f4f6 |

## Status Mapping

| Status | Color | Icon |
|--------|-------|------|
| Pending | Yellow | ○ |
| In Progress | Cyan | ▶ |
| Applied | Green | ✓ |
| Discarded | Red | ✗ |

## Implementation Progress

- [x] Core scaffold (entry point, main window, navigation)
- [x] Dashboard page
- [x] Jobs List page
- [x] Job Detail page
- [x] Profile page
- [x] Search page
- [x] Threading for async operations
- [ ] First-time setup wizard
- [ ] Settings dialog
- [ ] Add job dialog
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle

## Running the GUI

```bash
# Install PySide6 first (if not already installed)
pip install PySide6

# Run with GUI flag
./run.sh --gui
# or directly
cd src && python main.py --gui
# or use the standalone entry point
python src/gui_main.py
```

## Dependencies

Added to `requirements.txt`:
```
PySide6>=6.6.0
```

## Design Principles

1. **Consistency with CLI**: Same workflow, same terminology
2. **Non-blocking UI**: All long operations run in threads
3. **Progressive disclosure**: Show essential info first, details on demand
4. **Keyboard accessible**: Tab navigation, shortcuts for common actions
5. **Responsive**: Window resizing works well
6. **Platform native**: Use system colors where appropriate

## Style Guide

### Layout Hierarchy

```
Page
├── Page Header (large title, no container)
├── Card (white bg, border, rounded corners)
│   ├── Section Title (bold text, NO container)
│   ├── Content (plain text/labels, NO borders)
│   └── Actions (buttons in a row)
├── Card
│   └── ...
```

### Rule: One Container Per Section

**WRONG** - nested containers:
```
┌─ Card ──────────────────────────┐
│ ┌─ Title Container ──────────┐  │
│ │ Section Title              │  │
│ └────────────────────────────┘  │
│ ┌─ Content Container ────────┐  │
│ │ Some content here          │  │
│ └────────────────────────────┘  │
└─────────────────────────────────┘
```

**CORRECT** - flat structure:
```
┌─ Card ──────────────────────────┐
│ Section Title (just bold text)  │
│ Some content here (plain text)  │
│ More content                    │
│ [Button] [Button]               │
└─────────────────────────────────┘
```

### Component Styles

**Cards** (the ONLY bordered containers):
- White background
- 1px border `#e2e8f0`
- Border radius 12px
- Padding 20px

**Section Titles** (inside cards):
- Font size 16px
- Font weight 600 (semibold)
- Color `#1e293b`
- NO background, NO border
- Margin bottom 12px

**Labels/Content**:
- Font size 14px
- Color `#64748b` (muted) or `#1e293b` (primary)
- NO background, NO border

**Buttons**:
- Primary: Blue bg `#2563eb`, white text
- Secondary: Light gray bg `#f1f5f9`, dark text
- Danger: Red bg `#dc2626`, white text
- Padding 8px 16px, border-radius 6px

**Lists** (QListWidget):
- Border and background allowed (it's interactive)
- Inside a card, no extra wrapper

### What NOT to Do

1. Don't wrap labels in QFrame with borders
2. Don't give section titles their own background
3. Don't nest cards inside cards
4. Don't add borders to plain text content
5. Don't use CollapsibleSection inside cards (it adds its own container)
