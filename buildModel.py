import distances
from scipy.signal import wiener, filtfilt, butter, gaussian, freqz
import networkx

import matplotlib as mpl
from sklearn import linear_model
from sklearn import metrics
import operator

b, a = butter(5, 1.5/30.)


def fitGP(df, station, test_cut='6/1/2013', makePlot=True, showTest=True):
    '''do Gaussian process fit'''
    from sklearn.gaussian_process import GaussianProcess

    fitCols = [station, station+'_filtered']

    gp = GaussianProcess(regr='constant', corr='cubic')

    train = df[station+'_filtered'].truncate(after=test_cut)
    test = df[station+'_filtered'].truncate(before=test_cut)

    X = np.matrix(mpl.dates.date2num(train.index.to_pydatetime())).T
    y = train.values
    # Fit to data using Maximum Likelihood Estimation of the parameters
    gp.fit(X, y)

    xtest = np.matrix(mpl.dates.date2num(test.index.to_pydatetime())).T
    # Make the prediction on the meshed x-axis (ask for MSE as well)

    y_test, MSE = gp.predict(xtest, eval_MSE=True)
    sigma = np.sqrt(MSE)
    error = sigma

    y_train = gp.predict(X, eval_MSE=False)

    trainFull = df[station+'_filtered']
    X = np.matrix(mpl.dates.date2num(trainFull.index.to_pydatetime())).T
    y = trainFull.values
    # Fit to data using Maximum Likelihood Estimation of the parameters
    gp.fit(X, y)

    ix = pd.date_range('8/1/2014', '8/1/2020', freq='M')
    predx = np.matrix(mpl.dates.date2num(ix.to_pydatetime())).T
    y_pred, MSE_pred = gp.predict(predx, eval_MSE=True)
    trainDf = pd.DataFrame({'train': train,
                           'fit': y_train})
    testDf = pd.DataFrame({'test': test,
                           'y_test': y_test,
                           'sigma_test': sigma})
    test_score = metrics.r2_score(test.values, y_test)

    sigma_pred = np.sqrt(MSE_pred)
    predDf = pd.DataFrame({'y_pred': y_pred,
                           'sigma_pred': sigma_pred},
                          index=ix)
    result = pd.concat([trainDf, testDf, predDf], axis=1)
    result = pd.concat([result, df[fitCols]], axis=1)
    if makePlot:
        fig, ax = plt.subplots(1)
        ax.plot_date(X, y, 'g-', markersize=10, label=u'Observations')
        ax.plot_date(predx, y_pred, 'b-', label=u'Prediction')
        if showTest:
            ax.plot_date(test.index, y_test, 'r-')
            ax.plot_date(test.index, y_test - 1.96*sigma, 'r--')
            ax.plot_date(test.index, y_test + 1.96*sigma, 'r--')
        ax.plot_date(predx, y_pred - 1.96*sigma_pred, 'b--')
        ax.plot_date(predx, y_pred + 1.96*sigma_pred, 'b--')
        plt.xlabel('Date')
        plt.ylabel('Price per square foot')
    return result, test_score


def fitAR(df, station, test_cut='6/1/2013', order=(0, 2, 1),
          makePlot=True, showTest=True, doVAR=False):

    import statsmodels.api as sm

    fitCols = [station, station+'_filtered']

    train = df[station+'_filtered'].truncate(after=test_cut)
    test = df[station+'_filtered'].truncate(before=test_cut)
    full = df[station+'_filtered']

    arimaFullMod = sm.tsa.ARIMA(full, order=order)
    arimaTestMod = sm.tsa.ARIMA(train, order=order)
    arimaTestRes = arimaTestMod.fit()
    test_pred = arimaTestRes.predict(start=test.index[0].strftime('%m/%d/%Y'),
                                     end=test.index[-1].strftime('%m/%d/%Y'),
                                     typ='levels')
    test_score = metrics.r2_score(test.values, test_pred.values)

    arimaFullRes = arimaFullMod.fit()
    train_pred = arimaFullRes.predict(start=train.index[2].strftime('%m/%d/%Y'),
                                      end=train.index[-1].strftime('%m/%d/%Y'),
                                      typ='levels')

    trainDf = pd.DataFrame({'train': train,
                           'fit': train_pred})
    testDf = pd.DataFrame({'test': test,
                          'y_test': test_pred})
    predDf = arimaFullRes.predict(start=train.index[2].strftime('%m/%d/%Y'),
                                  end='2020', typ='levels')

    result = pd.concat([trainDf, testDf, predDf], axis=1)
    result = pd.concat([result, df[fitCols]], axis=1)

    if doVAR:
        allFiltered = [column for column in df.columns
                       if column.split('_')[-1] == 'filtered']

        trainVar = df[allFiltered].truncate(after=test_cut)
        testVar = df[allFiltered].truncate(before=test_cut)
        fullVar = df[allFiltered]

        testSteps = len(fullVar) - len(trainVar)

        varTrainMod = sm.tsa.VAR(trainVar[allFiltered])
        plt.close()
        varOrder = varTrainMod.select_order(32)
        varTrainRes = varTrainMod.fit(varOrder['aic'])
        order = varTrainRes.k_ar
        varTest = varTrainRes.forecast(trainVar[allFiltered].values[-order:],
                                       testSteps)

        varForeMod = sm.tsa.VAR(fullVar[allFiltered])
        varForeRes = varForeMod.fit(varOrder['aic'])
        order = varForeRes.k_ar
        foreSteps = 60
        varFore = varForeRes.forecast(fullVar[allFiltered].values[-order:],
                                      foreSteps)
        ix = pd.date_range(start=fullVar.index[-1].strftime('%m/%d/%Y'),
                           periods=foreSteps, freq='M')

        return var_res, varFore, ix

    if makePlot:
        arimaFullRes.plot_predict(start=train.index[2].strftime('%m/%d/%Y'),
                                  end='2020', dynamic=False)
        if showTest:
            test_pred.plot(color='red')
        plt.xlabel('Sell Date')
        plt.ylabel('Price per square foot')
        plt.xlim('2006', '2020')
    return result, test_score


def getPPSqft(df):
    '''Add ppSqf column to dataframe calculated from existing
    sellPrice and sqft columns'''

    df['sqft'][df['sqft'] == 0] = np.NAN
    df['ppSqf'] = (df['sellPrice'] /
                         df['sqft']).astype(float)
    return


def groupTimeavg(fulldata):
    '''Calculate monthly averaged price per square foot for each station'''
    stationFeature = {}
    grouped = fulldata.ix[:, ['sellData',
                              'nearestStation',
                              'ppSqf']].groupby('nearestStation')
    for station, group in grouped:
        group.index = group.sellData
        stationFeature[station] = group.resample("M", how='mean')
    return stationFeature


def processHistoricalData(fulldata, graph):
    '''Process listings data with distances into grouped-by-station
    times streams'''

    distances.getStationDistancesGraph(fulldata, graph)
    distances.getClosestStationsGraph(fulldata, graph)

    getPPSqft(fulldata)
    stationFeature = groupTimeavg(fulldata)
    for (name, info) in stationFeature.iteritems():
        info.columns = [name]
        info.index = pd.to_datetime(info.index)
        try:
            allStations = pd.concat([allStations, info], axis=1)
        except NameError:
            allStations = info

    # fix stations leftout because of duplicate names

    leftOut = (set(graph.nodes()) ^ set(allStations.columns))
    for station in leftOut:
        stationName = mapFromId[station]
        stations = list(n for n, d in graph.nodes_iter(data=True)
                        if d['name'] == stationName)
        if len(stations) > 1:
            print('%s: %s' % (station, mapFromId[station]))
            print stations
            keyStation = list(set(stations) & set(allStations.columns))
            allStations[station] = allStations[keyStation].mean(axis=1)

    # remove unresonable data points
    allStations[allStations > 4000] = np.NAN

    return allStations


def toSQL(df, tableName, dbName='mysql+mysqldb://root@localhost/iApp'):
    from sqlalchemy import create_engine
    engine = create_engine(dbName)
    df.to_sql(con=engine, name=tableName, if_exists='replace')


def dfBystop(stop, graph, allStations):
    '''Return dataframe with timelines for stations near input station and
    smoothed timelines'''

    mapFromId, mapToId = distances.getMappings(graph)
    subgraph = networkx.ego_graph(graph, stop, radius=5,
                                  undirected=True, distance='weight')
    columnNames = [mapFromId[node] for node in subgraph.nodes()]
    for station in subgraph.nodes():
        if station in allStations:
            filtered = filtfilt(b, a, allStations[station].interpolate().fillna(method='backfill'))
            stationDf = pd.DataFrame({station: allStations[station],
                                     (station + '_filtered'): filtered})
            try:
                tmpDf = pd.concat([tmpDf, stationDf], axis=1)
            except NameError:
                tmpDf = stationDf
    return tmpDf

if __name__ == "__main__":

    fulldata = util.pickle_load('data/fulldata_NOnearest_9-22.pkl')
    graph = util.pickle_load('subwaydata/NYCsubway_network_graph.pkl')
    mapFromId, mapToId = distances.getMappings(graph)

    allStations = processHistoricalData(fulldata, graph)
    station = mapToId['W 4 St']

    stationDf = dfBystop(station, graph, allStations)
    result = fitAR(stationDf, station, makePlot=True, order=(1, 1, 0),
                   showTest=True)
    stationDf = dfBystop(station, graph, allStations)
    result = fitGP(stationDf, station, showTest=True)

    # run GP for all stations and write to dB
    test_scores = {}
    for station in graph.nodes():
        if station in allStations:
            stationDf = dfBystop(station, graph, allStations)
            try:
                result, test_score = fitGP(stationDf, station)
                tableName = station+'_GPprediction'
                test_scores[station] = test_score

                # write to sql
                toSQL(result, tableName)
            except ValueError:
                continue
