# Census Folium Viewer:
# A set of functions for creating interactive choropleth maps
# of US Census Data using Folium
# By Kenneth Burchfiel 
# Released under the MIT license

# A sizeable portion of the choropleth mapping code
# came from Amodiovalerio Verde's excellent interactive
# choropleth tutorial at
# https://vverde.github.io/blob/interactivechoropleth.html .
# Amodiovalerio informed me via email that there are "no specific
# licences for the code of interactivechoropleth. 
# You're free to use the code. A mention/link will be appreciated."
# Thank you, Amodiovalerio!

import geopandas
import folium
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import numpy as np


def prepare_zip_table(shapefile_path, shape_feature_name, 
data_path, data_feature_name, tolerance = 0.005, dropna_geometry = True):
    '''This function merges US Census zip code shapefile data with
    Census zip-code-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.
    
    Variables:
    
    shapefile_path: The path to the .shp file that contains the shapefile 
    data (e.g. zip code boundaries) to include within the table.
    shape_feature_name: The name of the column within the shapefile table that
    contains the name of the shapes. For example, for the 2020 zip code
    shapefile data that I downloaded, the column name in the US Census
    shapefile happened to be ZCTA5CE20, and contained zip code names (22101,
    05753, etc).
    
    data_path: The path to a .csv file containing US Census data.
    
    data_feature_name: The name of the column within the US Census data .csv
    file that contains shape names (e.g. zip code boundaries). This column,
    along with the column referred to by shape_feature_name, will be used
    to merge the shapefile and US Census data tables together. 
    
    tolerance: The extent to which the shapefiles will be simplified.
    Lower tolerance values result in more accurate shape boundaries but also
    longer processing times and larger file sizes. I have found 0.005 to work
    pretty well for zip code maps.
    
    dropna_geometry: a boolean variable that determines whether or not to
    remove all rows from the data table that lack coordinates in the geometry
    column. This helps avoid 'NoneType' errors when producing maps. It 
    requires the geometry column to be named 'geometry.'

    '''

    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    shape_data[shape_feature_name] = shape_data[
        shape_feature_name].astype(str).str.pad(5, fillchar = '0')
    # The above line converts the zip code values into strings (if they were 
    # not already in that format), then adds extra 0s via str.pad to any
    # zip codes with fewer than 5 digits. This prevents data merging errors
    # related to zip codes with leading zeroes. For instance, if a shapefile
    # represented the zip 05753 as 5753, but a data file represented it as
    # 05753, the two zip codes would not merge. Adding in str.pad prevents
    # this issue.

    # To reduce the time needed to produce the choropleth map and to 
    # decrease its file size, the function next uses  Geopandas' simplify()
    # function to reduce the complexity of the shape coordinates stored in the
    # geometry column. See
    # https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.simplify.html
    # and (for more detail)
    # https://shapely.readthedocs.io/en/latest/manual.html#object.simplify .
    print("Simplifying shape data:") # This can take a little while
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    # The function next imports census data.
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    census_data[data_feature_name] = census_data[data_feature_name].astype(
        str).str.pad(5, fillchar = '0')
    # Since the zip codes in the shapefile data are in string format, the 
    # zip codes in the data file also need to be in string format.
    # Str.pad is used to ensure that all zip codes contain five digits, which
    # will help with the merging process. (str.zfill(5) would also work.)
    # Next, to make it easier to create choropleth maps, the function merges
    # the shapefile and census data tables.
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, 
    left_on = shape_feature_name, right_on = data_feature_name, how = 'outer')

    # An outer join is used so that the table can remain compatible with
    # additional datasets that are merged into this table. If an inner join
    # were used, all regions not found in the data table would be removed, 
    # limiting the table's versatility. 

    if dropna_geometry == True:
        merged_shape_data_table.dropna(subset = 'geometry', inplace = True)
    return merged_shape_data_table

def prepare_county_table(shapefile_path, shape_state_code_column, 
shape_county_code_column, tolerance, data_path, data_state_code_column, 
data_county_code_column, dropna_geometry = True):
    '''This function merges US Census county shapefile data with
    Census county-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.
    
    shape_state_code_column and shape_county_code_column refer to numerical
    state and county codes stored within the .shp shapefile document. 
    
    data_state_code_column and data_county_code_column refer to equivalent
    codes stored within the .csv Census data document. These codes will 
    be used to merge the shapefile and Census data tables together.
    
    See the documentation for prepare_zip_table for more information on
    this function.'''

    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    # The merge process for county-level data is based on state and county
    # codes because the 'NAME' value for the data and shape DataFrames
    # differs (see below). 
    # These numerical codes were stored within the US Census county 
    # shapefiles and county-level demographic data that I downloaded.
    # To help ensure that the merge process is successful, this function
    # converts the state and county codes for both tables into integer format.
    shape_data.rename(columns={'NAME':'SHORT_NAME'}, inplace = True) 
    # The 'NAME' column in the Census .shp file contains only the name of
    # the county (e.g. "Fairfax", whereas the 'NAME' column from the Census
    # data table also includes the state name (e.g. "Fairfax County,
    # Virginia"). Therefore, this column gets renamed above so that both
    # can exist within the merged DataFrame as distinct variables.
    shape_data[shape_state_code_column] = shape_data[
        shape_state_code_column].astype(int)
    shape_data[shape_county_code_column] = shape_data[
        shape_county_code_column].astype(int)
    print("Simplifying shape data:") 
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    census_data[data_state_code_column] = census_data[
        data_state_code_column].astype(int)
    census_data[data_county_code_column] = census_data[
        data_county_code_column].astype(int)
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, left_on = [
        shape_state_code_column, shape_county_code_column], right_on = [
            data_state_code_column, data_county_code_column], how = 'outer')
    if dropna_geometry == True:
        merged_shape_data_table.dropna(subset = 'geometry', inplace = True)
    return merged_shape_data_table


def prepare_state_table(shapefile_path, shape_feature_name, tolerance,
data_path, data_feature_name, dropna_geometry = True):
    '''This function merges US Census state shapefile data with
    Census state-level demographic data in order to create a DataFrame 
    that can be used to generate choropleth maps.

    See the documentation for prepare_zip_table for more information on
    this function.'''
    print("Reading shape data:")
    shape_data = geopandas.read_file(shapefile_path)
    print("Simplifying shape data:")
    shape_data['geometry'] = shape_data.simplify(tolerance = tolerance)
    print("Reading census data:")
    census_data = pd.read_csv(data_path)
    print("Merging shape and data tables:")
    merged_shape_data_table = pd.merge(shape_data, census_data, 
    left_on = shape_feature_name, right_on = data_feature_name, how = 'outer')
    if dropna_geometry == True:
        merged_shape_data_table.dropna(subset = 'geometry', inplace = True)
    return merged_shape_data_table




def render_map(merged_data_table, shape_feature_name, 
    data_variable, feature_text, map_name, html_save_path, 
    screenshot_save_path, data_variable_text = 'Value',
    popup_variable_text = 'Value',  variable_decimals = 4, 
    fill_color = 'Blues', rows_to_map = 0, bin_type = 'percentiles', 
    tiles = 'OpenStreetMap', generate_image = True, multiply_data_by = 1):
    '''
    (This code derives from old_generate_map within census_folium_viewer.py,
    available at https://github.com/kburchfiel/census_folium_tutorial .)

    This function uses a merged data table created through prepare_zip_table,
    prepare_county_table, or prepare_state_table to generate an interactive
    choropleth map in .html format. It then generates a .png version of 
    the map.

    Explanations of variables:

    merged_data_table: The merged data table created via prepare_zip_table,
    prepare_county_table, or prepare_state_table.

    shape_feature_name: The name of the column within the GeoDataFrame 
    containing unique IDs for each feature. It's very important that these are
    unique, as otherwise, values from one feature (e.g. a given Monroe County)
    may get copied onto other features with the same name (e.g. one of the
    other 16 Monroe Counties in the US). For counties, I recommend passing a
    column with values in (County, State) format to this argument 
    so that the map is more readable.

    data_variable: The name of the column containing the variable of interest
    (income, education level, etc.) to be graphed.

    feature_text: A string representing how the shape should be represented
    textually within the map.
    Examples would include "county", "zip", or "state."

    map_name: The string that will be used as the map's name when saving
    the .html and .png versions of the map.

    html_save_path: The path to the folder in which the .html version of the 
    map should be saved. This may need to be an absolute path, as 
    I encountered errors using a relative path. Legends will also be saved here.

    debug: When set to True, this function prints information about 
    what the function is about to perform.

    screenshot_save_path: The path to the folder in which the .html 
    version of the map should be saved. This can be a relative path. Note
    that, if specifying a screenshot_save_path value other than '', 
    you must create this path within your project folder before the
    function is run; otherwise, it won't return an image.

    data_variable_text: A string representing how the data variable should
    be represented textually within the map's legend.

    popup_variable_text: A string representing how the data variable should
    be represented textually within the box that displays when the user
    hovers over a given shape. It's best to keep this text short so that 
    the popup box does not become larger than necessary. For instance,
    if you're graphing median household income by county, data_variable_text
    could read "Median Household Income by County", but popup_variable_text
    can be simply "Income".

    variable_decimals: The number of decimals by which the data should be 
    rounded in the popup box.

    fill_color: The choropleth map's color pallette as sourced 
    from Color Brewer (see citation at the top of this page). 
    For color options, visit http://colorbrewer2.org/. The color code can be
    found within the URL corresponding to the color that you choose; 
    it's located in between &scheme= and &n. Examples of color codes 
    include 'RdYlGn' and 'Blues'. 
    
    rows_to_map: The number of rows in merged_data_table that should be mapped.
    If this value is set to 0, all rows will be mapped.
    Set rows_to_map to a lower amount to save rendering time when
    testing out different options.

    bin_type: The type of data bins used in the map's legend. The two options
    are 'percentiles' and 'equally_spaced.' equally_spaced is meant to 
    resemble the default bins option in Folium's choropleth map class,
    and creates bins of equal dimensions. Meanwhile, percentiles creates
    bins based on various equally spaced percentile points. You can experiment
    with both bin types to determine which option is best for your data.
    If outliers are present in your data, percentile-based bins may be ideal,
    as the color bins can otherwise be skewed by the outliers.

    tiles: The map data that you wish to use. Some additional
    options are listed at:
    https://deparkes.co.uk/2016/06/10/folium-map-tiles/ 

    generate_image: Specifies whether a .png version of the map should also
    be created. You can set it to false if you are having issues getting
    the Selenium code to work on your computer or if you don't need to get
    a screenshot of the map.

    multiply_data_by: The value by which the data should be multiplied prior to
    plotting the map. A value of 100, for example, will convert proportions to
    percents, whereas a value of 0.001 will convert a median income of 50,000
    to a value of 50.000. Tweaking this variable can help make the legend
    easier to read.
   
    Note: a sizeable portion of the following code, particularly the custom 
    choropleth mapping function and the code for the interactive overlay, 
    came from Amodiovalerio Verde's excellent interactive
    choropleth tutorial at
    https://vverde.github.io/blob/interactivechoropleth.html .
    Amodiovalerio informed me via email that there are "no specific
    licences for the code of interactivechoropleth. 
    You're free to use the code. A mention/link will be appreciated."
    Thank you, Amodiovalerio!
    
    This function also incorporates code from the choropleth example at:
    https://python-visualization.github.io/folium/quickstart.html      
    
    '''
    


    # The function will first drop rows in the table 
    # whose data variable column value is missing.
    merged_data_table_copy = merged_data_table.copy().dropna(
        subset = [data_variable]) 

    # It will then multiply all values in the data variable column by
    # the amount specified in multiply_data_by.
    merged_data_table_copy[data_variable] = merged_data_table_copy[
        data_variable]*multiply_data_by

    # Next, the values will get rounded by the value specified
    # in variable_decimals.
    merged_data_table_copy[data_variable] = merged_data_table_copy[
        data_variable].round(
        variable_decimals) # Rounds the data to be mapped. This needs to be
        # executed before the bins are calculated below in order to avoid
        # errors in which some data falls outside the bin dimensions.


    # The following lines limit the data to be mapped if a limit was entered
    # into the rows_to_map parameter. 
    if rows_to_map != 0: # A value of 0 means that all rows will be mapped.
        merged_data_table_copy = merged_data_table_copy.copy()[0:rows_to_map]
    print("Length of table is",len(merged_data_table_copy))

    if bin_type == 'percentiles':
    # This option creates bins that correspond to different percentiles
    # within the data.
        bins = np.percentile(merged_data_table_copy[data_variable].dropna(), 
        [0, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100])
        # https://numpy.org/doc/stable/reference/generated/numpy.percentile.html



    elif bin_type == 'equally_spaced':
        min_val = merged_data_table_copy[data_variable].min()
        max_val = merged_data_table_copy[data_variable].max()
        increment = (max_val - min_val)/8
        bins = list(np.arange(min_val, max_val, increment))
        bins.append(max_val)
        print(bins)
    # This option creates equally spaced bins. If outliers are skewing the 
    # data, this option may not be as ideal as the percentiles one.


    else:
        raise TypeError("Error: bin type not recognized. Bin type should be \
either 'percentiles' or 'equally spaced.'")


    # The function will now map the data:

    m = folium.Map(location=[38.7, -95], zoom_start=6, tiles = tiles)
    # The latitude and longitude were chosen so that, when a screenshot of 
    # the map was taken within Firefox via the code below, the legend and 
    # data labels would be on a relatively light surface within Candada.
    folium.Choropleth(
        geo_data=merged_data_table_copy,
        name="choropleth",
        data=merged_data_table_copy,
        columns=[shape_feature_name, data_variable],
        key_on="feature.properties."+shape_feature_name,
        # See the following page for more information on folium.Choropleth
        # and other folium features:
        # https://github.com/python-visualization/folium/blob/main/folium/features.py)        
        # I believe that the values stored in the list passed to the key_on 
        # parameter must equal those stored in the first entry within the 
        # columns parameter. That's why shape_feature_name is used for 
        # both entries here.
        fill_color = fill_color,
        bins = bins,
        fill_opacity=0.75, # Allows city names to be read underneath zip codes
        line_opacity=0.2, # Without outlines, it's harder to distinguish terrain 
        # from zip codes.
        legend_name=data_variable_text
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Next, I'll add overlays that display the name of the shape and its
    # value when the user hovers over it. 

    # The following code came from Amodiovalerio Verde's excellent interactive
    # choropleth tutorial at
    # https://vverde.github.io/blob/interactivechoropleth.html .
    # Amodiovalerio informed me via email that there are "no specific
    # licences for the code of interactivechoropleth. 
    # You're free to use the code. A mention/link will be appreciated."
    # Thank you, Amodiovalerio!


    style_function = lambda x: {'fillColor': '#ffffff', 
                                'color':'#000000', 
                                'fillOpacity': 0.1, 
                                'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.50, 
                                    'weight': 0.1}
    data_popup = folium.features.GeoJson(
        merged_data_table_copy,
        style_function=style_function, 
        control=False,
        highlight_function=highlight_function, 
        tooltip=folium.features.GeoJsonTooltip(
            fields=[shape_feature_name, data_variable],
            aliases=[feature_text, popup_variable_text],
            style=("background-color: white; color: #333333; font-family: \
            arial; font-size: 12px; padding: 10px;") 
        )
    )
    m.add_child(data_popup)
    m.keep_in_front(data_popup)
    folium.LayerControl().add_to(m)

    # Note: A simpler means of adding a tooltip to the map would look something like the following. [I haven't tested out this code within this function, however.]

    #     tooltip = folium.features.GeoJsonTooltip(fields = [shape_feature_name, data_variable], aliases = [feature_text, popup_variable_text)
    # # Based on https://python-visualization.github.io/folium/modules.html#folium.features.GeoJsonTooltip

    # folium.features.GeoJson(data = merged_data_table_copy, tooltip=tooltip, style_function = lambda x:{'opacity':0, 'fillOpacity':0}).add_to(m)

    # # Style function parameters come from https://leafletjs.com/SlavaUkraini/reference.html#path ; the format of style_function is based on one of the examples on https://python-visualization.github.io/folium/modules.html#folium.features.GeoJsonTooltip

    m.save(html_save_path+'\\'+map_name+'.html')


    # Finally, the function uses the Selenium library to create a screenshot 
    # of the map so that it can be shared as a .png file.
    # See https://www.selenium.dev/documentation/ for more information on 
    # Selenium. Note that some setup work is required for the Selenium code
    # to run correctly; if you don't have time right now to complete this 
    # setup, you can skip the screenshot generation process.


    if generate_image == True:

        ff_driver = webdriver.Firefox() 
        # See https://www.selenium.dev/documentation/webdriver/getting_started/open_browser/
        # For more information on using Selenium to get screenshots of .html 
        # files, see my get_screenshots.ipynb file within my route_maps_builder
        # program, available here:
        # https://github.com/kburchfiel/route_maps_builder/blob/master/get_screenshots.ipynb
        window_width = 3000 # This produces a large window that can better
        # capture small details (such as zip code shapefiles).
        ff_driver.set_window_size(window_width,window_width*(9/16)) # Creates
        # a window with an HD/4K/8K aspect ratio

        ff_driver.get(html_save_path+'\\'+map_name+'.html') 
        # See https://www.selenium.dev/documentation/webdriver/browser/navigation/
        time.sleep(2) # This gives the page sufficient
        # time to load the map tiles before the screenshot is taken. 
        # You can also experiment with longer sleep times.

        screenshot_image = ff_driver.get_screenshot_as_file(
            screenshot_save_path+'\\'+map_name+'.png') 
        # Based on:
        # https://www.selenium.dev/selenium/docs/api/java/org/openqa/selenium/TakesScreenshot.html

        ff_driver.quit()
        # Based on: https://www.selenium.dev/documentation/webdriver/browser/windows/

    return m