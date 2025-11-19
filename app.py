# %% Import + setup
import dash
from dash import html, Input, Output, State, ctx, dcc, Dash
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from credentials import sql_engine_string_generator
from flask import request
from datetime import datetime
import os
import logging
from dash_breakpoints import WindowBreakpoints
import socket
import dash.exceptions
import dash_ag_grid as dag
import re

# Local dev boolean
computer = socket.gethostname()
if computer == 'WONTN774787':
    local = True
else:
    local = False

# Version number to display
version = "4.0"

# Setup logger
if not os.path.exists('logs'):
    os.mkdir('logs')

logging.basicConfig(
    format='%(message)s',
    filename='logs/log.log',
    filemode='w+',
    level=20
)

logging.getLogger("azure").setLevel(logging.ERROR)

external_stylesheets=[
        dbc.themes.SLATE,
        "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css",
        '/assets/custom.css'
]
external_scripts = [
    "https://cdn.jsdelivr.net/npm/flatpickr",
    "https://cdn.jsdelivr.net/npm/inputmask/dist/inputmask.min.js"
]

# Initialize the dash app as 'app'
if not local:
    app = Dash(__name__,
               external_stylesheets=external_stylesheets, 
               external_scripts=external_scripts,
               requests_pathname_prefix="/app/AQPD/",
               routes_pathname_prefix="/app/AQPD/",
               suppress_callback_exceptions=True)
else:
    app = Dash(__name__,
               external_stylesheets=external_stylesheets, 
               external_scripts=external_scripts,
               suppress_callback_exceptions=True)

# Global variable to store headers
request_headers = {}

# Get connection string
dcp_sql_engine_string = sql_engine_string_generator('DATAHUB_PSQL_SERVER', 'dcp', 'DATAHUB_PSQL_USER', 'DATAHUB_PSQL_PASSWORD', local)
dcp_sql_engine = create_engine(dcp_sql_engine_string)

mercury_sql_engine_string = sql_engine_string_generator('DATAHUB_PSQL_SERVER', 'mercury_passive', 'DATAHUB_PSQL_USER', 'DATAHUB_PSQL_PASSWORD', local)
mercury_sql_engine = create_engine(mercury_sql_engine_string)


# Global storage for the new dataframe
database_df = pd.DataFrame(columns=[
    'sample_start', 'sample_end', 'sampleid', 'kitid', 'samplerid',
    'siteid', 'shipped_location', 'shipped_date', 'return_date',
    'sample_type', 'note', 'screen_sampling_rate'
])

# Global table headers dict
headerNames = {
    "sample_start": "Sample Start",
    "sample_end": "Sample End",
    "sampleid": "Sample ID",
    "kitid": "Kit ID",
    "samplerid": "Sampler ID",
    "siteid": "Site ID",
    "shipped_location": "Shipped Location",
    "shipped_date": "Shipped Date",
    "return_date": "Return Date",
    "sample_type": "Sample Type",
    "note": "Note"
}


# Define the placeholder for date/time columns
DATE_TIME_PLACEHOLDER = "YYYY-MM-DD HH:MM"

# Table div
global tablehtml


# %% Layout function, useful for having two UI options (e.g., mobile vs desktop)
def serve_layout():
    global databases
    global users
    global sites
    global sites_clean
    global tablehtml
    
    # Pull required data from tables
    users = pd.read_sql_table("users", dcp_sql_engine)
    sites = pd.read_sql_query("select * from stations", dcp_sql_engine)
    
    sites_clean = sorted([
        f"{row.description} ({row.siteid})"
        for _, row in sites.query("projectid == 'MERCURY_PASSIVE'").iterrows()
    ])
    
    dcp_sql_engine.dispose()
    mercury_sql_engine.dispose()
    
    
    tablehtml = html.Div(
        dag.AgGrid(
            id="database-table",
            enableEnterpriseModules=True,
            columnDefs=[
                {"field": "sample_start", "headerName": "Sample Start", "editable": True,"cellEditor": {"function": "DateTimePicker"}, "suppressSizeToFit": True, "width": 145},
                {"field": "sample_end", "headerName": "Sample End", "editable": True,"cellEditor": {"function": "DateTimePicker"}, "suppressSizeToFit": True, "width": 145},
                {"field": "sampleid", "headerName": "Sample ID", "editable": False, "suppressSizeToFit": True, "width": 156,"hide": True},
                {"field": "kitid", "headerName": "Kit ID", "editable": True, "suppressSizeToFit": True, "width": 100},
                {"field": "samplerid", "headerName": "Sampler ID", "editable": True, "suppressSizeToFit": True, "width": 127},
                #{"field": "siteid", "headerName": "Site ID", "editable": True, "suppressSizeToFit": True, "width": 150,
                # "cellEditor": "agRichSelectCellEditor","cellEditorParams": {"values": sites_clean,"searchEnabled": True,"filterList": True,}},
                {"field": "siteid", "headerName": "Site", "editable": True, "suppressSizeToFit": True, "width": 150,
                 "cellEditor": {"function": "SearchableDropdownEditor"},"cellEditorParams": {"values": sites_clean}},
                {"field": "shipped_location", "headerName": "Shipped Location", "editable": True, "suppressSizeToFit": True, "width": 165},
                {"field": "shipped_date","headerName": "Shipped Date","editable": True,"cellEditor": {"function": "DatePicker"},"suppressSizeToFit": True, "width": 146},
                {"field": "return_date", "headerName": "Return Date", "editable": True,"cellEditor": {"function": "DatePicker"},"suppressSizeToFit": True, "width": 133},
                {"field": "sample_type", "headerName": "Sample Type", "editable": True, "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["Sample", "Blank"]}, "suppressSizeToFit": True, "width": 130},
                {"field": "note", "headerName": "Note", "editable": True, "suppressSizeToFit": True, "width": 200}
            ],
            defaultColDef={"resizable": True, "sortable": True,"editable": True},
            columnSize="sizeToFit",
            dashGridOptions={"rowSelection":"single",
                             "animateRows": True,
                             "editable": True,
                             "enableRangeSelection": True,
                             "enableFillHandle": True,
                             "undoRedoCellEditing": True,
                             "undoRedoCellEditingLimit": 20,
                             "suppressClipboardPaste": False,
                             "components":{},
                             "loading": False
            },
            className="ag-theme-alpine-dark",
            style={"height": "400px", "width": "100%"}
        ),
        style={"padding": "0 40px"}
    )
    
    return html.Div([
        html.Div(id="display", style={'textAlign': 'center'}),
        WindowBreakpoints(
            id="breakpoints",
            widthBreakpointThresholdsPx=[768],
            widthBreakpointNames=["sm", "lg"]
        )
    ])

# %% Desktop layout
@app.callback(
    Output("display", "children"),
    Input("breakpoints", "widthBreakpoint"),
    State("breakpoints", "width"),
)
def change_layout(breakpoint_name: str, window_width: int):
    return [
        dbc.Row([
            html.H1('SampleTrack - Passive Mercury'),
            html.Span([
                f'v. {version} ',
                html.A(
                    "Documentation (how to use)",
                    href="https://github.com/ARQPDataTeam/qp_fieldnote_pas/blob/main/README.md",
                    target="_blank",
                    style={"color": "#66b3ff", "marginLeft": "10px", "fontSize": "0.9em"}
                )
            ]),
            html.Br(),
            html.Br(),
            html.Div([
                html.H3('Choose Sample Type:'),
                #html.Span('*', style={"color": "red", "font-weight": "bold"})
            ])
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Row(
                    dbc.Col([
                        dbc.Label(html.H2([
                            "User",
                            html.Span('*', style={"color": "red", "font-weight": "bold"})
                        ])),
                        html.Br(),
                        dcc.Input(
                            style={'textAlign': 'center'},
                            id="user",
                            autoComplete="off",
                            placeholder="..."
                        )
                    ]),
                    justify="center"
                ),
                id="user_div",
                width=3,
                align="center",
            )
        ], justify="center"),
        #html.Br(),
        dbc.Row(
            dbc.Col(
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button("New", id="btn-new", color="primary"),
                        dbc.Button("Update", id="btn-update", color="secondary")
                    ], size="md"),
                    dbc.Tooltip("Create new sample entry", target="btn-new", placement="top"),
                    dbc.Tooltip("Update existing sample entry", target="btn-update", placement="top"),
                ]),
                width="auto",
            ),
            justify="center",
            className="buttons_div"
        ),
        dcc.Loading(
            id="db-loading-wrapper",
            type="default",  # You can also use "circle" or "dot"
            children=html.Div(id="db-loading-output", style={"display": "inline-block"})
        ),
        html.Hr(),
        tablehtml,
        html.Div(id="edit-confirmation", style={"textAlign": "center", "color": "green", "marginTop": "10px"}),
        dbc.Modal(
            id="new-entry-modal",
            is_open=False,
            size="lg",
            children=[
                dbc.ModalHeader("Enter New Kit Information"),
                dbc.ModalBody([
                    # Sampler IDs header
                    html.H5("Sampler IDs", className="mb-3 text-center"),
                    html.Div(id="entry-container", children=[]),
                    # Kit ID section
                    dbc.Row(
                        dbc.Col([
                            html.H5("Kit ID", className="mb-2 text-center"),
                            dbc.Input(
                                id="static-kit-id-input",
                                type="text",
                                placeholder="EC-XXXX",
                                autoComplete="off",
                                className="text-center",
                                style={'width': '150px', 'margin': '0 auto'}
                            ),
                        ],
                        className="d-flex flex-column align-items-center"),
                        justify="center",
                        className="mb-4 mt-4"
                    ),
                    # Loading animation below Kit ID
                    html.Div([
                        dbc.Spinner(color="primary", type="grow"),
                        html.Span(" Waiting for user input...", className="text-muted ms-2")
                    ], className="text-center my-3"),
                ]),
                dbc.ModalFooter(
                    [
                        dbc.Button("Done", id="new-done-button", color="success"),
                        html.Div(id="new-kitid-feedback", className="mt-3 text-center")
                    ],
                    className="w-100 d-flex flex-column align-items-center"
                )
            ]
        ),
        dbc.Modal(
            id="update-kitid-modal",
            is_open=False,
            size="md",
            children=[
                dbc.ModalHeader("Update Kit Entry"),
                dbc.ModalBody([
                    html.H5("Search by:", className="mb-2 text-center"),
                    dbc.RadioItems(
                        id="update-search-mode",
                        options=[
                            {"label": "Kit ID", "value": "kit"},
                            {"label": "Sampler ID", "value": "sampler"},
                            {"label": "Shipped Location", "value": "location"}
                        ],
                        value="kit",
                        inline=True,
                        className="mb-3 d-flex justify-content-center text-light"
                    ),
                    html.H5("Enter ID", className="mb-2 text-center"),
                    html.Div([
                        dbc.Input(
                            id="update-kitid-textinput",
                            type="text",
                            autoComplete="off",
                            placeholder="EC-XXXX",
                            className="text-center",
                            persistence=True,
                            persistence_type='session',
                            style={'width': '150px', 'margin': '0 auto', 'display': 'block'}
                        ),
                        dcc.Dropdown(
                            id="update-kitid-dropdown",
                            options=[],  # To be set dynamically
                            placeholder="Select a Shipped Location",
                            searchable=True,
                            clearable=False,
                            persistence=True,
                            persistence_type='session',
                            style={'width': '250px', 'margin': '0 auto', 'display': 'none'}
                        )
                    ], id="update-id-input-container"),
                    html.Div(id="update-kitid-feedback", className="mt-3 text-center")
                ]),
                dbc.ModalFooter(
                    dbc.Button("Done", id="update-done-button", color="success"),
                    className="w-100 d-flex justify-content-center"
                )
            ]
        ),
        dcc.Store(id="entry-store", data=[]),
        dcc.Store(id="editing", data=False),
        dcc.Store(id="entry-counter", data=1),
        dcc.Store(id='database-store', data=[]),
        dcc.Store(id="kitid-filtered-data", data=None),
        dcc.Interval(id='log_updater', interval=5000),
        html.Div(
            dbc.Button(
                "Upload Data to Database",
                id="btn-upload-data",
                color="success",
                className="mt-4",
                style={'display': 'none'} 
            ),
            className="d-flex justify-content-center"
        ),
        
        html.Div(
            dbc.Button(
                "Download Database as CSV",
                id="btn-download-db",
                color="info",
                className="mt-2",
            ),
            className="d-flex justify-content-center"
        ),
        
        dcc.Download(id="download-db-csv"),
        dbc.Modal(
            id="overwrite-confirm-modal",
            is_open=False,
            children=[
                dbc.ModalHeader("Overwrite Confirmation"),
                dbc.ModalBody("Some sample IDs already exist in the database. Do you want to overwrite them?"),
                dbc.ModalFooter([
                    dbc.Button("Yes, Overwrite", id="confirm-overwrite", color="danger", className="me-2"),
                    dbc.Button("Cancel", id="cancel-overwrite", color="secondary")
                ])
            ]
        ),
        dcc.Store(id="duplicate-rows", data=[]),
        dcc.Store(id="overwrite-confirmed", data=False)
    ]

# %% Function to create textbox rows
def create_text_row(index: int, value="", editable=True, selection=None):
    return html.Div(
        id={'type': 'entry-row', 'index': index},
        children=[
            dbc.Input(
                id={'type': 'entry-input', 'index': index},
                type="text",
                value=value,
                placeholder="ECCCXXXX",
                autoComplete="off",
                disabled=not editable,
                debounce=False,
                className="mb-2 me-2"
            ),
            dcc.RadioItems(
                id={'type': 'entry-radio', 'index': index},
                options=[
                    {'label': 'Sample', 'value': 'Sample'},
                    {'label': 'Blank', 'value': 'Blank'}
                ],
                value=selection,
                labelStyle={'display': 'inline-block', 'marginRight': '10px'},
                inputStyle={"marginRight": "5px"},
                style={'marginBottom': '10px', 'color': 'white'}
            ),
            dbc.Button("×", id={'type': 'delete-row', 'index': index}, color="danger", size="sm", className="ms-2")
        ],
        className="d-flex align-items-center",
        style={'gap': '20px', 'marginBottom': '10px'}
    )

# %% Modal for "new" button click
@app.callback(
    Output("new-entry-modal", "is_open"),
    Output("entry-container", "children", allow_duplicate=True),
    Output("entry-store", "data", allow_duplicate=True),
    Output("editing", "data", allow_duplicate=True),
    Output("entry-counter", "data"),
    Input("btn-new", "n_clicks"),
    Input("new-done-button", "n_clicks"),
    State("new-entry-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(new_clicks, done_clicks, is_open):
    triggered_id = ctx.triggered_id
    if triggered_id == "btn-new":
        return True, [create_text_row(1)], [{"index": 1, "value": "", "editable": True, "radio": None}], False, 2
    elif triggered_id == "new-done-button":
        return False, [], [], False, 1
    return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# %% Create text boxes dynamically in "New" modal
@app.callback(
    Output("entry-container", "children", allow_duplicate=True),
    Output("entry-store", "data", allow_duplicate=True),
    Output("entry-counter", "data", allow_duplicate=True),
    Input({'type': 'entry-input', 'index': dash.ALL}, 'value'),
    Input({'type': 'entry-radio', 'index': dash.ALL}, 'value'),
    State({'type': 'entry-input', 'index': dash.ALL}, 'id'),
    State("entry-counter", "data"),
    prevent_initial_call=True
)
def update_entry_store_and_ui(values, radios, ids, counter):
    if not values or not ids:
        raise dash.exceptions.PreventUpdate

    new_data = []
    new_components = []
    seen_indices = set()

    for i, id_obj in enumerate(ids):
        idx = id_obj['index']
        seen_indices.add(idx)
        value = values[i] if i < len(values) else ""
        radio = radios[i] if i < len(radios) else None

        new_data.append({
            "index": idx,
            "value": value,
            "editable": True,
            "radio": radio
        })

        new_components.append(create_text_row(idx, value=value, editable=True, selection=radio))

    if isinstance(values[-1], str) and len(values[-1]) == 8 and counter not in seen_indices:
        new_data.append({
            "index": counter,
            "value": "",
            "editable": True,
            "radio": None
        })
        new_components.append(create_text_row(counter, value="", editable=True))
        counter += 1

    return new_components, new_data, counter


# %% Delete row callback
@app.callback(
    Output("entry-container", "children", allow_duplicate=True),
    Output("entry-store", "data", allow_duplicate=True),
    Input({'type': 'delete-row', 'index': dash.ALL}, 'n_clicks'),
    State("entry-store", "data"),
    prevent_initial_call=True
)
def delete_row(delete_clicks, entry_data):
    if not any(delete_clicks):
        raise dash.exceptions.PreventUpdate

    triggered = ctx.triggered_id
    if not triggered:
        raise dash.exceptions.PreventUpdate

    delete_index = triggered['index']
    new_data = [row for row in entry_data if row['index'] != delete_index]
    new_components = [
        create_text_row(row['index'], row['value'], editable=True, selection=row['radio'])
        for row in new_data
    ]
    return new_components, new_data


# %% "Done" button callback for new entries
@app.callback(
    Output("database-table", "rowData", allow_duplicate=True),
    Output("btn-upload-data", "style", allow_duplicate=True),
    Output("new-kitid-feedback", "children"),
    Output("new-kitid-feedback", "style"),
    Output("new-entry-modal", "is_open", allow_duplicate=True),
    Output("entry-container", "children", allow_duplicate=True),
    Output("entry-store", "data", allow_duplicate=True),
    Input("new-done-button", "n_clicks"),
    State("static-kit-id-input", "value"),
    State("entry-store", "data"),
    State("entry-container", "children"),
    prevent_initial_call=True
)
def validate_and_build_df(n_clicks, kit_id_value, entry_data, current_components):
    global database_df

    # Validate Kit ID
    if not kit_id_value or not re.fullmatch(r"EC-\d{4}", kit_id_value.strip()):
        return dash.no_update, dash.no_update, "Invalid Kit ID format. Expected EC-####.", {"color": "red"}, True, current_components, entry_data

    # Validate Sample IDs
    invalid_samples = [
        entry["value"] for entry in entry_data
        if entry.get("value") and not re.fullmatch(r"ECCC\d{4}", entry["value"].strip())
    ]
    if invalid_samples:
        return dash.no_update, dash.no_update, f"Invalid Sample ID(s): {', '.join(invalid_samples)}. Expected ECCC####.", {"color": "red"}, True, current_components, entry_data

    # Proceed with building the DataFrame
    valid_entries = [entry for entry in entry_data if entry.get("value", "").strip() != ""]
    records = []
    for entry in valid_entries:
        sampler_id = entry.get("value", "")
        generated_sampleid = f"{kit_id_value}_{sampler_id}" if kit_id_value and sampler_id else None
        records.append({
            'sample_start': None,
            'sample_end': None,
            'sampleid': generated_sampleid,
            'kitid': kit_id_value,
            'samplerid': sampler_id,
            'siteid': None,
            'shipped_location': None,
            'shipped_date': None,
            'return_date': None,
            'sample_type': entry.get("radio", ""),
            'note': None,
            'screen_sampling_rate': None
        })

    database_df = pd.DataFrame(records)
    return database_df.to_dict("records"), {'display': 'block', 'margin-top': '20px'}, "", {"color": "green"}, False, current_components, entry_data


# %% Update df whenever user edits the datatable
@app.callback(
    Output("edit-confirmation", "children",allow_duplicate=True),
    Output("database-table", "rowData"),
    Input("database-table", "cellValueChanged"),
    State("database-table", "rowData"),
    prevent_initial_call=True
)
def sync_table_edits(cellValueChanged, current_grid_data):
    global database_df
    if not cellValueChanged:
        raise dash.exceptions.PreventUpdate

    changed_col = cellValueChanged[0]['colId']
    user_friendly_col = headerNames.get(changed_col, changed_col)
    changed_row_index = cellValueChanged[0]['rowIndex']
    user_friendly_row = changed_row_index + 1
    new_value_raw = cellValueChanged[0]['value']
    old_value = cellValueChanged[0]['oldValue']

    updated_grid_data = list(current_grid_data)

    feedback_message = ""
    feedback_style = {"color": "green"}

    # Update the value in the grid data first
    if changed_col in ['sample_start', 'sample_end']:
        if new_value_raw:
            strict_dt_regex = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"

            if not re.fullmatch(strict_dt_regex, str(new_value_raw)):
                updated_grid_data[changed_row_index][changed_col] = old_value if old_value is not None else ""
                feedback_message = f"Invalid datetime format for {user_friendly_col} at Row {user_friendly_row}. Expected format: YYYY-MM-DD HH:MM."
                feedback_style = {"color": "red"}
            else:
                updated_grid_data[changed_row_index][changed_col] = new_value_raw
                feedback_message = f"{user_friendly_col} at Row {user_friendly_row}, changed from '{old_value}' to '{new_value_raw}'."
                feedback_style = {"color": "green"}
        else:
            updated_grid_data[changed_row_index][changed_col] = "" # Keep as empty string if user clears it in UI
            feedback_message = f"{user_friendly_col} at Row {user_friendly_row}, value cleared."
            feedback_style = {"color": "green"}
    else:
        updated_grid_data[changed_row_index][changed_col] = new_value_raw
        feedback_message = f"{user_friendly_col} at Row {user_friendly_row}, changed from '{old_value}' to '{new_value_raw}'."
        feedback_style = {"color": "green"}

    # After updating the changed cell, check if sampleid needs to be updated
    if changed_col in ['kitid', 'samplerid']:
        row = updated_grid_data[changed_row_index]
        current_kitid = row.get('kitid') if row.get('kitid') is not None else ""
        current_samplerid = row.get('samplerid') if row.get('samplerid') is not None else ""
        
        # Construct the new sampleid
        new_sampleid = f"{current_kitid}_{current_samplerid}"
        
        # Only update if the sampleid actually changes to avoid unnecessary re-renders
        if row.get('sampleid') != new_sampleid:
            updated_grid_data[changed_row_index]['sampleid'] = new_sampleid
            # Also update feedback message to indicate sampleid was updated
            feedback_message += f" Sample ID updated to '{new_sampleid}'."


    database_df = pd.DataFrame(updated_grid_data)
    database_df.to_csv("debug_database_df.csv",index =False)

    return html.Div(feedback_message, style=feedback_style), updated_grid_data


# %% Grab user email from headers
@app.callback(
    Output('user', 'value'),
    Output('user', 'disabled'),
    Output('user_div', 'style'),
    Input('user', 'id')
)
def display_headers(_):
    if request_headers.get('Dh-User'):
        return [request.headers.get('Dh-User'), True, {'display': 'none'}]
    else:
        return [None, False, {'display': 'none'}]

@app.server.before_request
def before_request():
    global request_headers
    request_headers = dict(request.headers)  # Capture headers before processing any request


# %% javascript used to autofocus newly created textboxes in "New" modal
app.clientside_callback(
    """
    function(children) {
        window.requestAnimationFrame(() => {
            setTimeout(() => {
                const container = document.getElementById('entry-container');
                if (container) {
                    const inputs = container.querySelectorAll('input[type="text"]');
                    if (inputs.length > 0) {
                        inputs[inputs.length - 1].focus();
                    }
                }
            }, 100);
        });
        return children;
    }
    """,
    Output("entry-container", "children", allow_duplicate=True),
    Input("entry-container", "children"),
    prevent_initial_call=True
)

# %% Upload Data button with duplicates checking
@app.callback(
    Output("edit-confirmation", "children", allow_duplicate=True),
    Output("overwrite-confirm-modal", "is_open"),
    Output("duplicate-rows", "data"),
    Input("btn-upload-data", "n_clicks"),
    prevent_initial_call=True
)
def upload_data_to_database(n_clicks):
    global database_df 

    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    
    siteid_map = {
        f"{row.description} ({row.siteid})": row.siteid
        for _, row in sites.query("projectid == 'MERCURY_PASSIVE'").iterrows()
    }

    
    # Check if table is empty
    df_to_upload = database_df[database_df['samplerid'].astype(str).str.strip() != ''].copy()
    if df_to_upload.empty:
        return html.Div("No valid data to upload. All entries are empty or have empty Sampler IDs.", style={"color": "orange"}), False, []
    
    # Convert columns to datetime
    for col in ['sample_start', 'sample_end', 'shipped_date', 'return_date']:
        df_to_upload[col] = pd.to_datetime(df_to_upload[col], errors='coerce')

        # Convert any timezone-aware datetimes to naive
        if pd.api.types.is_datetime64tz_dtype(df_to_upload[col]):
            df_to_upload[col] = df_to_upload[col].dt.tz_convert(None)
    
        # Drop tzinfo even from objects that were naive-but-strange
        df_to_upload[col] = df_to_upload[col].dt.tz_localize(None)
    
        # Format to ensure no millisecond or tzinfo remnants
        df_to_upload[col] = df_to_upload[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        
    # Upload
    try:
        existing_sampleids_df = pd.read_sql_query("SELECT sampleid FROM pas_tracking", mercury_sql_engine)
        existing_sampleids = set(existing_sampleids_df['sampleid'].dropna().astype(str).tolist())

        df_to_upload_sampleids = df_to_upload['sampleid'].astype(str)
        duplicate_mask = df_to_upload_sampleids.isin(existing_sampleids)

        if duplicate_mask.any():
            duplicate_df = df_to_upload[duplicate_mask].copy()
            return dash.no_update, True, duplicate_df.to_dict("records")
        
        df_to_upload['siteid'] = df_to_upload['siteid'].map(siteid_map).fillna(df_to_upload['siteid']) # change column to only contain siteid
        df_to_upload.to_sql('pas_tracking', mercury_sql_engine, if_exists='append', index=False)
        return html.Div(f"Successfully uploaded {len(df_to_upload)} new entries to 'pas_tracking' table!", style={"color": "green"}), False, []

    except Exception as e:
        logging.error(f"Database upload error: {e}")
        return html.Div(f"Error uploading data: {e}.", style={"color": "red"}), False, []
    
# %% Update button callback
@app.callback(
    Output("update-kitid-modal", "is_open", allow_duplicate=True),
    Output("database-store", "data"),
    Output("db-loading-output", "children"),
    Input("btn-update", "n_clicks"),
    Input("update-done-button", "n_clicks"),
    State("update-kitid-modal", "is_open"),
    State("database-store", "data"),
    prevent_initial_call=True
)
def toggle_update_modal(open_clicks, done_clicks, is_open, db_tracking_data):
    triggered = ctx.triggered_id

    if triggered == "btn-update":
        # Show loading while querying database
        try:
            db_df = pd.read_sql_query("SELECT * FROM pas_tracking", mercury_sql_engine)
            for col in ["sample_start", "sample_end"]:
                if col in db_df.columns:
                    db_df[col] = pd.to_datetime(db_df[col], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
            loading_msg = ""  # Hide loading spinner
        except Exception as e:
            logging.error(f"Error loading pas_tracking table: {e}")
            db_df = pd.DataFrame()
            loading_msg = ""  # Hide loading even on error

        return True, db_df.to_dict("records"), loading_msg

    elif triggered == "update-done-button":
        return False, db_tracking_data, ""  # Closing modal, no DB call = no spinner

    return is_open, db_tracking_data, ""

# %% Confirm overwrite
@app.callback(
    Output("edit-confirmation", "children",allow_duplicate=True),
    Output("overwrite-confirm-modal", "is_open",allow_duplicate=True),
    Input("confirm-overwrite", "n_clicks"),
    State("duplicate-rows", "data"),
    prevent_initial_call=True
)
def confirm_overwrite(n_clicks, duplicates_data):
    if not duplicates_data:
        raise dash.exceptions.PreventUpdate

    try:
        df_overwrite = pd.DataFrame(duplicates_data)
        df_overwrite.replace('', np.nan, inplace=True)

        with mercury_sql_engine.begin() as conn:
            sampleids = df_overwrite['sampleid'].dropna().tolist()
            for sid in sampleids:
                conn.execute(text("DELETE FROM pas_tracking WHERE sampleid = :sid"), {"sid": sid})

        df_overwrite.to_sql('pas_tracking', mercury_sql_engine, if_exists='append', index=False)

        return html.Div(f"Successfully overwrote {len(df_overwrite)} entries.", style={"color": "green"}), False

    except Exception as e:
        logging.error(f"Overwrite failed: {e}")
        return html.Div(f"Error overwriting: {e}", style={"color": "red"}), False

# %% Cancel overwrite
@app.callback(
    Output("overwrite-confirm-modal", "is_open",allow_duplicate=True),
    Input("cancel-overwrite", "n_clicks"),
    prevent_initial_call=True
)
def cancel_overwrite(n):
    return False

# %% Update Done button callback
@app.callback(
    Output("update-kitid-feedback", "children"),
    Output("update-kitid-feedback", "style"),
    Output("update-kitid-modal", "is_open", allow_duplicate=True),
    Output("database-table", "rowData", allow_duplicate=True),
    Output("kitid-filtered-data", "data"),
    Output("btn-upload-data", "style", allow_duplicate=True),
    Input("update-done-button", "n_clicks"),
    State("update-kitid-textinput", "value"),
    State("update-kitid-dropdown", "value"),
    State("database-store", "data"),
    State("update-search-mode", "value"),
    prevent_initial_call=True
)
def validate_and_display_kitid(n_clicks, text_value, dropdown_value, db_tracking_data, search_mode):
    entered_id = dropdown_value if search_mode == "location" else text_value
    
    db_tracking_data = pd.DataFrame(db_tracking_data)
    
    # Kit ID search logic
    if search_mode == "kit":
        if not re.fullmatch(r"EC-\d{4}", entered_id.strip()):
            return "Invalid Kit ID", {"color": "red"}, True, dash.no_update, dash.no_update, dash.no_update
        filtered_df = db_tracking_data[db_tracking_data['kitid'] == entered_id]
    #Location search logic
    elif search_mode == "location":
        if not entered_id.strip():
            return "Shipped Location cannot be empty.", {"color": "red"}, True, dash.no_update, dash.no_update, dash.no_update
    
        matches = db_tracking_data[
            db_tracking_data["shipped_location"].str.strip().str.lower() == entered_id.strip().lower()
        ].copy()
    
        if matches.empty:
            return f"No entries found for shipped location '{entered_id}'.", {"color": "orange"}, True, dash.no_update, dash.no_update, dash.no_update
    
        filtered_df = matches
    # Sampler ID search logic 
    else:
        if not re.fullmatch(r"ECCC\d{4}", entered_id.strip()):
            return "Invalid Sampler ID", {"color": "red"}, True, dash.no_update, dash.no_update, dash.no_update
    
        matches = db_tracking_data[db_tracking_data['samplerid'] == entered_id].copy()
    
        if matches.empty:
            return "No entries found for this Sampler ID.", {"color": "orange"}, True, dash.no_update, dash.no_update, dash.no_update
    
        # Most recent sample_start (fallback to index if missing)
        if "sample_start" in matches.columns:
            matches["sample_start"] = pd.to_datetime(matches["sample_start"], errors="coerce")
            matches = matches.sort_values("sample_start", ascending=False)
        
        recent_kitid = matches["kitid"].dropna().iloc[0]
        filtered_df = db_tracking_data[db_tracking_data["kitid"] == recent_kitid]

    if filtered_df.empty:
        return "No entries found for this Kit ID.", {"color": "orange"}, True, dash.no_update, dash.no_update, dash.no_update
    
    # Update global dataframe
    filtered_df["sample_start"] = filtered_df["sample_start"].str.slice(stop=16)
    filtered_df["sample_end"] = filtered_df["sample_end"].str.slice(stop=16)
    filtered_df["siteid"] = filtered_df["siteid"].apply(
        lambda x: next(
            (s for s in sites_clean if isinstance(x, str) and x.strip() and x in s),
            x
        )
    )
    global database_df
    database_df = filtered_df

    return "", {}, False, database_df.to_dict("records"), filtered_df.to_dict("records"),{"display": "block", "margin-top": "20px"}



# %% Dynamic input switch for update modal
@app.callback(
    Output("update-kitid-textinput", "style"),
    Output("update-kitid-dropdown", "style"),
    Output("update-kitid-textinput", "placeholder"),
    Output("update-kitid-dropdown", "options"),
    Input("update-search-mode", "value"),
    State("database-store", "data")
)
def toggle_update_input(search_mode, db_data):
    show_text = {'width': '150px', 'margin': '0 auto', 'display': 'block'}
    hide_text = {'width': '150px', 'margin': '0 auto', 'display': 'none'}
    show_dropdown = {'width': '250px', 'margin': '0 auto', 'display': 'block'}
    hide_dropdown = {'width': '250px', 'margin': '0 auto', 'display': 'none'}

    if search_mode == "location":
        db_df = pd.DataFrame(db_data)
        locations = sorted(db_df["shipped_location"].dropna().unique().tolist())
        return hide_text, show_dropdown, dash.no_update, [{"label": loc, "value": loc} for loc in locations]

    elif search_mode == "sampler":
        return show_text, hide_dropdown, "ECCCXXXX", []

    # default to Kit ID
    return show_text, hide_dropdown, "EC-XXXX", []

# %% Callback to trigger download of most recent database contents
@app.callback(
    Output("download-db-csv", "data"),
    Input("btn-download-db", "n_clicks"),
    prevent_initial_call=True
)
def download_db_csv(n_clicks):
    try:
        db_df = pd.read_sql_query("SELECT * FROM pas_tracking", mercury_sql_engine)
        for col in ["sample_start", "sample_end"]:
            if col in db_df.columns:
                db_df[col] = pd.to_datetime(db_df[col], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
        now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"pas_tracking_{now_str}.csv"
        return dcc.send_data_frame(db_df.to_csv, filename=filename, index=False)
    except Exception as e:
        logging.error(f"Error exporting pas_tracking to CSV: {e}")
        return dash.no_update



# %% Run app
app.layout = serve_layout

if not local:
    server = app.server
else:
    if __name__ == '__main__':
        app.run(debug=True, port=8080)
