import seaborn as sns
import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import errno
import statsmodels.stats.proportion as smp
from matplotlib.patches import Rectangle

def create_custom_palette():
    tool_colors = {
        "DeepHyperion": "#d3d3d3",
        "DeepJanus": "#d3d3d3",  # C0C0C0 - #DCDCDC
        "DLFuzz": "#a9a9a9",  # #808080
        "IlluminatedAsFault": "#ffffff"  # #808080
    }
    return tool_colors



def rename_features(features):
    return [rename_feature(f) for f in features]


def abbreviate_feature(feature):
    if "Bitmaps" == feature or "bitmaps" == feature:
        return "Luminosity"
    elif "Moves" == feature or "moves" == feature:
        return "Moves"
    elif "Orientation" == feature or "orientation" == feature:
        return "Orientation"
    ##
    elif "Segment Count" == feature or "segment_count" == feature:
        return "Turn Count"
    elif "MinRadius" == feature or "min_radius" == feature:
        return "Min Radius"
    elif "MeanLateralPosition" == feature or "mean_lateral_position" == feature:
        return "Mean Lateral Position"
    elif "SDSteeringAngle" == feature or "sd_steering" == feature:
        return "Std Steering Angle"

def rename_feature(feature):
    if "Bitmaps" == feature or "bitmaps" == feature:
        return "Lum"
    elif "Moves" == feature or "moves" == feature:
        return "Mov"
    elif "Orientation" == feature or "orientation" == feature:
        return "Or"
    ##
    elif "Segment Count" == feature or "segment_count" == feature:
        return "TurnCnt"
    elif "MinRadius" == feature or "min_radius" == feature:
        return "MinRad"
    elif "MeanLateralPosition" == feature or "mean_lateral_position" == feature:
        return "MLP"
    elif "SDSteeringAngle" == feature or "sd_steering" == feature:
        return "StdSA"


def load_data_from_folder(dataset_folder, allowed_features_combination=None):
    """
    Returns: Panda DF with the data about the experiments from the data folder, data/mnist or data/beamng. Merge the configurations of DH together
    -------
    """

    the_data = None

    for subdir, dirs, files in os.walk(dataset_folder, followlinks=False):

        # Consider only the files that match the pattern
        for json_data_file in [os.path.join(subdir, f) for f in files if f.endswith("stats.json")]:

            with open(json_data_file, 'r') as input_file:
                # Get the JSON
                map_dict = json.load(input_file)

                # Introduce a value to uniquely identify the tool combinations (Important fo DH)
                map_dict["Tool"] = map_dict["Tool"].replace("BeamNG", "")
                map_dict["Tool"] = map_dict["Tool"].replace("Rerun", "")

                # "Expose" the reports by flattening the JSON
                # TODO We rely on the fact that there's ONLY one report here
                assert len(map_dict["Reports"]) == 1, "Too many reports to plot !"
                skip = False
                for report_idx, report_dict in enumerate(map_dict["Reports"]):

                    target_feature_combination = "-".join(rename_features(report_dict["Features"]))

                    if allowed_features_combination is not None and not target_feature_combination in allowed_features_combination:
                        print("SKIP Feature Combination ", target_feature_combination)
                        skip = True
                        continue
                    else:
                        map_dict["Features Combination"] = target_feature_combination
                        for item in [i for i in report_dict.items() if i[0] != "Features"]:
                            map_dict[item[0]] = item[1]


                # Patch: Do not any data if there's no feature combination
                if skip:
                    continue

                if the_data is None:
                    # Creates the DataFrame
                    the_data = pd.json_normalize(map_dict)
                else:
                    # Maybe better to concatenate only once
                    the_data = pd.concat([the_data, pd.json_normalize(map_dict)])

    # make sure that DH is reported per each configuration
    # https://stackoverflow.com/questions/26886653/pandas-create-new-column-based-on-values-from-other-columns-apply-a-function-o

    # # TODO Improve the labeling - Let's do this directly at the level of JSON
    # fn = lambda row: row.Tool + '-'.join(row.Tags) if row.Tool == "DeepHyperionBeamNG" else row.Tool  # define a function for the new column
    # col = beamng_data.apply(fn, axis=1)  # get column data with an index
    # beamng_data = beamng_data.assign(**{'Tool Configuration': col.values})

    # Fix data type
    the_data['Tags'] = the_data['Tags'].astype(str)
    print("Loaded data for:", the_data["Tool"].unique())
    print("\tFeatures Combinations:", the_data["Features Combination"].unique())
    return the_data


def filter_data_by_tag(raw_data, tags):
    # Keep only the data which contain the tags. Ideally one should
    # simply check for containment in the Tags column,
    # but this somehow gets the d64 type instead of string...
    # Load data and store that into the context for the next commands
    # This is how we filter white-box and black-box data

    filtered_data = raw_data
    for tag in tags:
            filtered_data = filtered_data[filtered_data['Tags'].str.contains(tag)]
    return filtered_data


# Utility to plot maps data
def filter_data_and_plot_as_boxplots(use_ax, we_plot, raw_data, palette):

    assert type(we_plot) is str, "we_plot not a string !"

    # Select only the data we need to plot
    plot_axis_and_grouping = [
        "Tool",  # Test Subjects
        "Features Combination"  # Features that define this map
    ]
    # Filter the data
    we_need = plot_axis_and_grouping[:]
    we_need.append(we_plot)
    plot_data = raw_data[we_need]

    if plot_data.empty:
        print("WARINING: Empty plot !")
        return None

    hue_order = []
    for tool_name in ["DeepHyperion", "IlluminatedAsFault"]: #["DeepHyperion", "DeepJanus", "DLFuzz", "IlluminatedAsFault"]:
        if tool_name in plot_data["Tool"].unique():
            hue_order.append(tool_name)

    # Return the axis to allow for additional changes
    return sns.boxplot(x="Features Combination",
                     y=we_plot,
                     hue="Tool",
                     data=plot_data,
                     palette=palette,
                     hue_order=hue_order,
                     ax=use_ax)


# TODO For the moment look only at white box data
def load_probability_maps(dataset_folder, type="white-box"):

    rows_list = []
    for subdir, dirs, files in os.walk(dataset_folder, followlinks=False):

        # Extract metadata about features
        for json_data_file in [os.path.join(subdir, f) for f in files if
                         f.startswith("DeepHyperion") and
                         (f.endswith("-"+type+"-rescaled-stats.json") or f.endswith("-"+type+"-relative-stats.json"))]:

            with open(json_data_file, 'r') as input_file:
                # Get the JSON
                map_dict = json.load(input_file)

            # TODO Read those from the json maybe?
            # DLFuzz-017-Orientation-Moves-"+type+"-rescaled-stats.json
            attrs = json_data_file.split("-")

            run = attrs[1]
            map_type = attrs[6].replace("-stats.npy", "")

            # Store the features data for this run - Is this a tuple ?!
            features = tuple(map_dict["Features"].keys())

            for feature_name, f in map_dict["Features"].items():
                rows_list.append({
                    'bins': [np.linspace(f["meta"]["min-value"], f["meta"]["max-value"], f["meta"]["num-cells"])],
                    'feature': feature_name,
                    'features': features,
                    'map type': map_type,
                    'run': int(run)
                })

    # Feature Map
    features_data = pd.DataFrame(rows_list, columns={'bins': pd.Series([], dtype='float'),
                                                     'features': pd.Series([], dtype='str'),
                                                     'feature': str(),
                                                     'map type': str(),
                                                     'run': int()})

    rows_list = []
    for subdir, dirs, files in os.walk(dataset_folder, followlinks=False):
        # Consider only the files that match the pattern
        for npy_file in [os.path.join(subdir, f) for f in files if
                         f.startswith("probability-DeepHyperion") and
                         (f.endswith("-"+type+"-rescaled.npy") or f.endswith("-"+type+"-relative.npy"))]:

            probabilities = np.load(npy_file)
            attrs = npy_file.split("-")
            # probability-DeepJanusBeamNG-001-segment_count-sd_steering-SegmentCount-SDSteeringAngle-"+type+"-rescaled.npy
            features = (attrs[3], attrs[4])
            map_type = attrs[9].replace(".npy", "")
            run = attrs[2]

            rows_list.append({
                'probabilities': probabilities,
                'features': features,
                'map type': map_type,
                'run': int(run)
            })

    probability_data = pd.DataFrame(rows_list, columns={'probabilities': pd.Series([], dtype='float'),
                                          'features': pd.Series([], dtype='str'),
                                          'map type': str(),
                                          'run': int()})

    rows_list = []
    for subdir, dirs, files in os.walk(dataset_folder, followlinks=False):
        # Consider only the files that match the pattern
        for npy_file in [os.path.join(subdir, f) for f in files if
                                              f.startswith("misbehaviour-DeepHyperion") and
                                              (f.endswith("-"+type+"-rescaled.npy") or f.endswith(
                                                  "-"+type+"-relative.npy"))]:
            misbehaviors = np.load(npy_file)
            attrs = npy_file.split("-")

            features = (attrs[3], attrs[4])
            map_type = attrs[9].replace(".npy", "")
            run = attrs[2]


            rows_list.append({
                'misbehaviors': misbehaviors,
                'features': features,
                'map type': map_type,
                'run': int(run)
            })

    misbehavior_data = pd.DataFrame(rows_list, columns={'misbehaviors': pd.Series([], dtype='float'),
                                                            'features': pd.Series([], dtype='str'),
                                                            'map type': str(),
                                                            'run': int()})

    rows_list = []
    for subdir, dirs, files in os.walk(dataset_folder, followlinks=False):
        # Consider only the files that match the pattern
        for npy_file in [os.path.join(subdir, f) for f in files if
                      f.startswith("coverage-DeepHyperion") and
                      (f.endswith("-"+type+"-rescaled.npy") or f.endswith(
                          "-"+type+"-relative.npy"))]:
            coverage = np.load(npy_file)
            attrs = npy_file.split("-")

            features = (attrs[3], attrs[4])
            map_type = attrs[9].replace(".npy", "")
            run = attrs[2]

            rows_list.append({
                'coverage': coverage,
                'features': features,
                'map type': map_type,
                'run': int(run)
            })

    # merge all the DF to obtain the last one
    coverage_data = pd.DataFrame(rows_list, columns={'coverage': pd.Series([], dtype='float'),
                                                        'features': pd.Series([], dtype='str'),
                                                        'map type': str(),
                                                        'run': int()})
    df = probability_data.merge(misbehavior_data, on=['features', 'map type', 'run'])
    df = df.merge(coverage_data, on=['features', 'map type', 'run'])

    return df, features_data


def set_probability_maps_axes(ax, features_df, features, map_type, fontsize=24, min_fontsize=20):

    try:
        # Prepare the labels and ticks (reused across main map and supporting maps)
        f1_bins = list(features_df[(features_df["features"] == features) & (features_df["map type"] == map_type)
                                   & (features_df["feature"] == features[0])]["bins"].array[0][0])
        f2_bins = list(features_df[(features_df["features"] == features) & (features_df["map type"] == map_type)
                                   & (features_df["feature"] == features[1])]["bins"].array[0][0])

        ax.set_xticks(np.linspace(0, len(f1_bins)-1, len(f1_bins)))
        ax.set_yticks(np.linspace(0, len(f2_bins)-1, len(f2_bins)))

        # [unicode(x.strip()) if x is not None else '' for x in row]
        xtickslabel = [round(the_bin, 1) if idx % 2 == 0 else '' for idx, the_bin in enumerate(f1_bins)]
        ytickslabel = [round(the_bin, 1) if idx %2 == 0 else '' for idx, the_bin in enumerate(f2_bins)]

        ax.set_xticklabels(xtickslabel, fontsize=min_fontsize, rotation=45)
        ax.set_yticklabels(ytickslabel, fontsize=min_fontsize, rotation=0)


        ax.set_xlabel(rename_feature(features[0]), fontsize=fontsize)
        ax.set_ylabel(rename_feature(features[1]), fontsize=fontsize)

        # Add rotation


        # We need this to have the y axis start from zero at the bottom
        ax.invert_yaxis()

        # axis labels
        plt.xlabel(rename_feature(features[0]), fontsize=14)
        plt.ylabel(rename_feature(features[1]), fontsize=14)
    except Exception as e:
        print("Error in setting axes for", features, map_type)
        print(e)


def enumerate2D(array1, array2):
    """
    https://stackoverflow.com/questions/44117612/enumerate-over-2-arrays-of-same-shape
    """
    assert array1.shape == array2.shape, "Error - dimensions."
    for indexes, data in np.ndenumerate(array1):
        yield indexes, data, array2[indexes]



def generate_average_probability_maps(use_ax, probability_df, features,
                                      min_avg_prob=0.7999, min_low_ci=0.64999):

    # Take all the probability maps for rescaled
    map_type = "rescaled"

    all_probabilities = list(probability_df[(probability_df["features"] == features) &
                                            (probability_df["map type"] == map_type)]["probabilities"])
    # Compute the mean ignoring Nan over the cells
    avg_probabilities = np.nanmean(all_probabilities, axis=0)

    # Load misb and coverage
    all_misbehaviors = list(probability_df[(probability_df["features"] == features) & (
            probability_df["map type"] == map_type)]["misbehaviors"])
    all_coverage = list(probability_df[(probability_df["features"] == features) & (
                probability_df["map type"] == map_type)]["coverage"])

    # Sum per each cell
    total_misb = np.nansum(all_misbehaviors, axis=0)
    total_inputs = np.nansum(all_coverage, axis=0)

    # Compute the confidence intervals per cell
    confident_data_high = np.empty(shape=total_misb.shape, dtype=float)
    confident_data_high[:] = np.NaN
    confident_data_low = np.empty(shape=total_misb.shape, dtype=float)
    confident_data_low[:] = np.NaN

    for (i, j), value in np.ndenumerate(total_misb):

        if np.isnan(value):
            continue

        (low, high) = smp.proportion_confint(value, total_inputs[i][j], method='wilson')
        confident_data_high[i][j] = high
        confident_data_low[i][j] = low

    # Transpose to have first axis over x
    avg_probabilities = np.transpose(avg_probabilities)
    confident_data_high = np.transpose(confident_data_high)
    confident_data_low = np.transpose(confident_data_low)
    total_inputs = np.transpose(total_inputs)
    total_misb = np.transpose(total_misb)

    # Create the color map
    cmap = sns.cubehelix_palette(50, hue=0.05, rot=0, light=0.9, dark=0.5, as_cmap=True)
    # Set WHITE for the cells for which we do not have observations (NaN)
    cmap.set_bad(color='white')
    # Show the average probabilities in the map


    use_ax = sns.heatmap(avg_probabilities,
                         square=True,
                         vmin=0.0, vmax=1.0,
                         cmap=cmap,
                         cbar=None,
                         linewidths=1,
                         ax=use_ax
                         )

    # Highlighted cells: each cell is an empty square with a tick border.
    # Highlight the cells that value above 0.8 and low_ci above 0.65.
    # Note that we have j, i not i, j because we transposed the original data while here
    # we use the ax reference system and not the heatmap one
    for (j, i), prob_value, low_ci_value in enumerate2D(avg_probabilities, confident_data_low):
        if prob_value > min_avg_prob and low_ci_value > min_low_ci:
            use_ax.add_patch(Rectangle((i, j), 1, 1, fill=False, edgecolor='black', lw=2))

    return use_ax



PAPER_FOLDER="./plots"

def store_figure_to_paper_folder(figure, file_name):
    import os
    try:
        os.makedirs(PAPER_FOLDER)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    file_format = 'pdf'
    figure_file_name = "".join([file_name, ".", file_format])
    figure_file = os.path.join(PAPER_FOLDER, figure_file_name)

    # https://stackoverflow.com/questions/4042192/reduce-left-and-right-margins-in-matplotlib-plot
    figure.tight_layout()
    figure.savefig(figure_file, format=file_format, bbox_inches='tight')

    print("Plot stored to ", figure_file)
