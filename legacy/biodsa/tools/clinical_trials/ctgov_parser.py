import pandas as pd
import json
import logging
import traceback

def parse_ctgov_json_response(response_content:dict):
    total_count = response_content.get("totalCount", "Unknown")
    # get nextPageToken
    next_page_token = response_content.get("nextPageToken", None)
    results = response_content.get("studies", {})
    if len(results) == 0:
        return "No results found.", total_count, None
    studies = []
    for res in results:
        res = parse_json_studies_response(res)
        studies.append(res)
    studies = pd.concat(studies, axis=0).reset_index(drop=True)

    return studies, total_count, next_page_token


def parse_json_studies_response(
    response: dict,
    ):
    """Parse the retrieved json trial info from CT.gov.
    Index(['NCT Number', 'Study Title', 'Study URL', 'Acronym', 'Study Status',
        'Brief Summary', 'Study Results', 'Conditions', 'Interventions',
        'Primary Outcome Measures', 'Secondary Outcome Measures',
        'Other Outcome Measures', 'Sponsor', 'Collaborators', 'Sex', 'Age',
        'Phases', 'Enrollment', 'Funder Type', 'Study Type', 'Study Design',
        'Other IDs', 'Start Date', 'Primary Completion Date', 'Completion Date',
        'First Posted', 'Results First Posted', 'Last Update Posted',
        'Locations', 'Study Documents']

    if target_fields is None, default to a subset of fields to be parsed and returned to save time.
    if target_fields is given, parse and return the given fields plus the default fields.
    """
    data = response.get("protocolSection", {})
    nct_number = data.get('identificationModule', {}).get('nctId', None)
    study_title = data.get('identificationModule', {}).get('briefTitle', None)
    study_url = f'https://clinicaltrials.gov/ct2/show/{nct_number}' if nct_number else None
    study_status = data.get('statusModule', {}).get('overallStatus', None)
    brief_summary = data.get('descriptionModule', {}).get('briefSummary', None)
    primary_outcome_measures = data.get('outcomesModule', {}).get('primaryOutcomes', [{}])[0].get('measure', None)
    secondary_outcome_measures = '|'.join([outcome.get('measure', None) for outcome in data.get('outcomesModule', {}).get('secondaryOutcomes', [])])
    sponsor = data.get('sponsorCollaboratorsModule', {}).get('leadSponsor', {}).get('name', None)
    collaborators = '|'.join([collaborator.get('name', None) for collaborator in data.get('sponsorCollaboratorsModule', {}).get('collaborators', [])])
    sex = data.get('eligibilityModule', {}).get('sex', None)
    min_age = data.get('eligibilityModule', {}).get('minimumAge', None)
    max_age = data.get('eligibilityModule', {}).get('maximumAge', None)
    age = f"{min_age} - {max_age}" if min_age and max_age else None
    phases = '|'.join(data.get('designModule', {}).get('phases', []))
    enrollment = data.get('designModule', {}).get('enrollmentInfo', {}).get('count', None)
    study_type = data.get('designModule', {}).get('studyType', None)
    study_design = data.get('designModule', {}).get('designInfo', {}).get('interventionModel', None)
    start_date = data.get('statusModule', {}).get('startDateStruct', {}).get('date', None)
    primary_completion_date = data.get('statusModule', {}).get('primaryCompletionDateStruct', {}).get('date', None)
    completion_date = data.get('statusModule', {}).get('completionDateStruct', {}).get('date', None)
    first_posted = data.get('statusModule', {}).get('studyFirstSubmitDate', None)
    last_update_posted = data.get('statusModule', {}).get('lastUpdatePostDateStruct', {}).get('date', None)
    locations = '|'.join([f"{location.get('facility', '')}, {location.get('city', '')}, {location.get('state', '')}, {location.get('country', '')}" for location in data.get('contactsLocationsModule', {}).get('locations', [])])
    eligibility = data.get('eligibilityModule', {}).get('eligibilityCriteria', None)
    interventions = '|'.join([x.get('name', "") for x in data.get('armsInterventionsModule', {}).get('interventions', [])])
    conditions = '|'.join(data.get('conditionsModule', {}).get('conditions', []))

    investigators = '|'.join([f"{investigator.get('name', '')}, {investigator.get('affiliation', '')}" for investigator in data.get("contactsLocationsModule", {}).get('overallOfficials', [])])
    if len(investigators) == 0:
        investigators = '|'.join([f"{investigator.get('name', '')}, {investigator.get('affiliation', '')}" for investigator in data.get("contactsLocationsModule", {}).get('centralContacts', [])])
        investigators = f"Central Contacts: {investigators}; Locations: {locations}"

    # parse the interventional arm design info
    arm_design = data.get('armsInterventionsModule', {}).get('armGroups', [])
    if len(arm_design) > 0:
        arm_design = ["{}:{}".format(arm.get('type',f'arm{str(i)}'), arm.get('label', f'intervention{str(i)}')) for i,arm in enumerate(arm_design)]
        arm_design = '|'.join(arm_design)
    else:
        arm_design = None

    group_val_str = None
    group_ae_str = None
    group_baseline_str = None
    if response.get("hasResults", False):
        result_section = response.get("resultsSection", {})

        # parse to get endpoint results
        outcome_measure_module = result_section.get("outcomeMeasuresModule", {})
        try:
            df_outcome = parse_json_outcome_module_to_dataframe(outcome_measure_module)
            df_outcome = df_outcome.rename(columns={"Group ID":"Arm ID", "Group Title": "Arm Title"})
            if len(df_outcome) > 0:
                # aggregate group ID and title
                groupid_to_title_str = dataframe_to_json(df_outcome[["Arm ID", "Arm Title"]].drop_duplicates(), orient="records")

                # aggregate by arm
                df_outcome = df_outcome[df_outcome["Measure Title"].map(len) > 0].reset_index(drop=True)
                arm_measure_vals = df_outcome[["Arm ID","Measure Title", "Measurement Value"]]
                arm_measure_vals = dataframe_to_json(arm_measure_vals, orient="records")

                group_val_str = {
                    "Group Definition": groupid_to_title_str,
                    "Arm-wise Values": arm_measure_vals,
                    "Trial ID": nct_number,
                }
                group_val_str = json.dumps(group_val_str)
        except:
            logging.error(traceback.format_exc())
            group_val_str = {
                "Group Definition": None,
                "Aggregate Values": None,
                "Arm-wise Values": None,
            }
            group_val_str = json.dumps(group_val_str)

        # parse to get AE results
        serious_ae_module = result_section.get("adverseEventsModule", {})

        # TODO
        # transform the module to a dataframe
        # generate code to get insights from the dataframe later
        try:
            df_serious_ae = parse_json_serious_ae_module_to_dataframe(serious_ae_module)
            if len(df_serious_ae) > 0:
                # aggregate group ID and title
                groupid_to_title_str = df_serious_ae[["Group ID", "Group Title"]].drop_duplicates().groupby("Group ID")["Group Title"].apply(lambda x: '|'.join(x)).reset_index()
                groupid_to_title_str = groupid_to_title_str.to_json(orient="records")

                # aggregate AE by arm-wise
                df_serious_ae["Event Cases"] = df_serious_ae["Term"] + ": " + df_serious_ae["Number of Events"].astype(str)
                arm_ae_str = df_serious_ae[["Group ID", "Event Cases"]].groupby("Group ID")["Event Cases"].apply(lambda x: '|'.join(x)).reset_index()
                arm_ae_str = aggregate_dataframe_to_string(arm_ae_str, row_sep="\n", col_sep="; ")

                # aggregate by event
                top_aes = df_serious_ae[["Term","Number of Events"]].groupby("Term")["Number of Events"].sum().reset_index()
                top_aes = top_aes.sort_values(by="Number of Events", ascending=False).reset_index(drop=True)[:5]
                group_ae_str = {
                    "Group Definition": groupid_to_title_str,
                    "Aggregate Values": top_aes.set_index("Term")["Number of Events"].to_json(),
                    "Arm-wise Values": arm_ae_str,
                    "Trial ID": nct_number,
                }
                group_ae_str = json.dumps(group_ae_str)

            else:
                group_ae_str = {
                    "Group Definition": None,
                    "Aggregate Values": None,
                    "Arm-wise Values": None,
                }
                group_ae_str = json.dumps(group_ae_str)
        except:
            logging.error(traceback.format_exc())
            group_ae_str = {
                "Group Definition": None,
                "Aggregate Values": None,
                "Arm-wise Values": None,
            }
            group_ae_str = json.dumps(group_ae_str)

        # parse to get participant characteristics
        baseline_module = result_section.get("baselineCharacteristicsModule", {})
        try:
            df_baseline = parse_json_baseline_module_to_dataframe(baseline_module)
            if len(df_baseline) > 0:
                # aggregate group ID and title
                groupid_to_title_str = df_baseline[["Group ID", "Group Title"]].drop_duplicates().groupby("Group ID")["Group Title"].apply(lambda x: '|'.join(x)).reset_index()
                groupid_to_title_str = aggregate_dataframe_to_string(groupid_to_title_str)
                
                df_baseline["Baselines"] = df_baseline["Value"].apply(lambda x: float(x) if is_numeric(x) else None)
                df_baseline = df_baseline[df_baseline["Baselines"].notnull()].reset_index(drop=True)
                agg_bs_str = df_baseline[["Category Title", "Baselines"]].groupby("Category Title").agg("sum").reset_index()
                agg_bs_str.columns = ["Category", "Number"]
                agg_bs_str = agg_bs_str[agg_bs_str["Number"] > 0].reset_index(drop=True)
                agg_bs_str = agg_bs_str.set_index("Category")["Number"].to_json()

                group_baseline_str = {
                    "Group Definition": groupid_to_title_str,
                    "Aggregate Values": agg_bs_str,
                }
                group_baseline_str = json.dumps(group_baseline_str)

        except:
            logging.error(traceback.format_exc())
            group_baseline_str = {
                "Group Definition": None,
                "Aggregate Values": None,
            }
            group_baseline_str = json.dumps(group_baseline_str)


    # Create a DataFrame
    df = pd.DataFrame({
        'NCT Number': [nct_number],
        'Study Title': [study_title],
        'Study URL': [study_url],
        'Study Status': [study_status],
        'Brief Summary': [brief_summary],
        'Conditions': [conditions],
        'Interventions': [interventions],
        'Primary Outcome Measures': [primary_outcome_measures],
        'Secondary Outcome Measures': [secondary_outcome_measures],
        'Sponsor': [sponsor],
        'Collaborators': [collaborators],
        'Sex': [sex],
        'Age': [age],
        'Phases': [phases],
        'Enrollment': [enrollment],
        'Study Type': [study_type],
        'Study Design': [study_design],
        'Start Date': [start_date],
        'Primary Completion Date': [primary_completion_date],
        'Completion Date': [completion_date],
        'First Posted': [first_posted],
        'Last Update Posted': [last_update_posted],
        'Locations': [locations],
        'Eligibility Criteria': [eligibility],
        'Investigators': [investigators],
        'Arm Design': [arm_design],
        'Study Results': [group_val_str],
        'Serious Adverse Events': [group_ae_str],
        'Participant Baselines': [group_baseline_str],
    })

    return df


def is_numeric(s):
    s = s.replace(',', '')
    try:
        float(s)
        return True
    except ValueError:
        return False

def parse_json_baseline_module_to_dataframe(data):
    # get group id to arm name mapping
    groups = data.get("groups", [])
    group_name_to_id = []
    for group in groups:
        group_id = group.get("id", "")
        group_title = group.get("title", "")
        group_name_to_id.append({
            "Group ID": group_id,
            "Group Title": group_title
        })
    group_name_to_id = pd.DataFrame(group_name_to_id)


    # get baseline measurements
    measures = data.get("measures", [])
    if len(measures) == 0:
        return []
    
    outputs = []
    for measure in measures:
        measure_title = measure.get('title', '')
        classes = measure.get('classes', [])
        classes = classes[0] if len(classes) > 0 else {}
        classes = classes.get('categories', [])
        if len(classes) == 0:
            continue

        for category in classes:
            category_title = category.get('title', '')
            measurements = category.get('measurements', [])
            for measurement in measurements:
                group_id = measurement.get('groupId', '')
                value = measurement.get('value', '')
                if value == "":
                    continue

                title = measure_title + ":" + category_title if category_title != "" else measure_title
                outputs.append({
                    'Category Title': title,
                    'Group ID': group_id,
                    'Value': value
                })

    df = pd.DataFrame(outputs)
    
    df = df.merge(group_name_to_id, on="Group ID", how="left")

    return df


def aggregate_dataframe_to_string(df, col_sep="|*|", row_sep="\n"):
    preview_str = df.fillna("NA").astype(str).apply(lambda x: x.name + " : "+x)
    preview_str = preview_str.agg(col_sep.join, axis=1)
    preview_str = row_sep.join(preview_str.tolist())
    return preview_str

def dataframe_to_json(df, orient="split"):
    """convert dataframe to dictionary"""
    if isinstance(df, pd.DataFrame):
        return df.to_dict(orient=orient)
    elif isinstance(df, pd.Series):
        return df.to_dict()
    else:
        return None

def parse_json_serious_ae_module_to_dataframe(data):
    serious_ae = data.get('seriousEvents', [])
    if len(serious_ae) == 0:
        return []
    
    # get group id to arm name mapping
    groups = data.get("eventGroups", [])
    group_name_to_id = []
    for group in groups:
        group_id = group.get("id", "")
        group_title = group.get("title", "")
        group_name_to_id.append({
            "Group ID": group_id,
            "Group Title": group_title
        })
    group_name_to_id = pd.DataFrame(group_name_to_id)
    
    outputs = []
    for term in serious_ae:
        term_name = term.get('term', '')
        stats = term.get('stats', [])
        for stat in stats:
            group_id = stat.get('groupId', '')
            num_event = stat.get('numEvents', 0)
            outputs.append({
                'Term': term_name,
                'Group ID': group_id,
                'Number of Events': num_event
            })
        
    df = pd.DataFrame(outputs)
    df = df[df["Number of Events"] > 0].reset_index(drop=True)
    df = df.merge(group_name_to_id, on="Group ID", how="left")
    return df

def parse_json_outcome_module_to_dataframe(data):
    outcome_measures = data.get('outcomeMeasures', [])

    rows = []

    for measure in outcome_measures:
        measure_type = measure.get('type', '')
        measure_title = measure.get('title', '')
        measure_description = measure.get('description', '')
        measure_reporting_status = measure.get('reportingStatus', '')
        measure_param_type = measure.get('paramType', '')
        measure_time_frame = measure.get('timeFrame', '')

        for group in measure.get('groups', []):
            group_id = group.get('id', '')
            group_title = group.get('title', '')
            group_description = group.get('description', '')

            denoms = measure.get('denoms', [{}])[0].get('counts', [])
            denom_value = next((item['value'] for item in denoms if item.get('groupId') == group_id), '')

            for category in measure.get('classes', [{}])[0].get('categories', []):
                category_title = category.get('title', '')
                measurements = category.get('measurements', [])
                measurement_value = next((item['value'] for item in measurements if item.get('groupId') == group_id), '')
                if measurement_value == "NA" or len(str(measurement_value)) == 0:
                    measurement_value = None
                row = {
                    'Measure Type': measure_type,
                    'Measure Title': measure_title,
                    'Measure Description': measure_description,
                    'Reporting Status': measure_reporting_status,
                    'Parameter Type': measure_param_type,
                    'Time Frame': measure_time_frame,
                    'Group ID': group_id,
                    'Group Title': group_title,
                    'Group Description': group_description,
                    'Denom ID': denom_value,
                    'Category Title': category_title,
                    'Measurement Value': measurement_value
                }

                rows.append(row)

    df = pd.DataFrame(rows)

    return df