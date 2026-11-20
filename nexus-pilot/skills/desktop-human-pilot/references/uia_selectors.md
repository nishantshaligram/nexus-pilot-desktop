# Windows UI Automation (UIA) Selectors & Control Taxonomy

Reference for querying semantic elements using `inspect_ui_tree` and `find_element`.

## Standard Control Types

| ControlType | Description | Typical Interaction |
|---|---|---|
| `Button` | Push buttons, tool buttons, toolbar items | `click_element(query="Save")` |
| `Edit` | Text fields, single/multi-line inputs | Click to focus, then `send_keystrokes(text="...")` |
| `CheckBox` | Toggleable checkbox controls | `click_element(...)` |
| `RadioButton` | Mutually exclusive radio buttons | `click_element(...)` |
| `ComboBox` | Dropdown selection lists | Click to expand, then arrow keys or child click |
| `MenuItem` | Menu items in menu bars or context menus | `click_element(...)` |
| `TabItem` | Document tabs or property page tabs | `click_element(...)` |
| `Hyperlink` | Clickable text links | `click_element(...)` |
| `ListItem` | Items within list views or tables | `click_element(...)` or double click |
| `TreeItem` | Nodes in tree views (e.g. Solution Explorer) | Click or double click to expand |

## Selector Matching Heuristics

`find_element` and `click_element` perform case-insensitive substring matching on:
1. `name`: The visible accessibility label or text content (e.g. `"OK"`, `"Cancel"`, `"Save Changes"`).
2. `id`: The programmatic `AutomationId` assigned by developers (e.g. `"btn_submit"`, `"txt_username"`).

If multiple controls share a name, qualify the search by passing `window_title` to restrict the search tree.
