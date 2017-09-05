from feature import Feature
import numpy as np


class ScoreFairValueFeature(Feature):

    @classmethod
    def computeForInstrument(cls, featureParams, featureKey, currentFeatures, instrument, instrumentManager):
        lookbackDataDf = instrument.getDataDf()
        predictionKey = 'prediction'
        price = 'close'
        countKey = 'count'
        if len(lookbackDataDf) < 1 or instrumentManager is None:
            return 0
        lookbackMarketDataDf = instrumentManager.getDataDf()
        if 'predictionKey' in featureParams:
            predictionKey = featureParams['predictionKey']
        if 'price' in featureParams:
            price = featureParams['price']
        if 'countKey' in featureParams:
            countKey = featureParams['countKey']
        if len(lookbackMarketDataDf) < 1:
            # first iteration
            return 0
        predictionDict = lookbackMarketDataDf[predictionKey].iloc[-1]
        prevCount = lookbackMarketDataDf[countKey].iloc[-1]
        if len(predictionDict) == 0 or prevCount == 0:
            return 0
        prevData = lookbackDataDf[featureKey].iloc[-1]

        temp = (prevCount - 1) * (prevData**2)

        sqError = (predictionDict[instrument.getInstrumentId()] - lookbackDataDf[price].iloc[-1])**2
        temp = (temp + sqError)
        # print(currentFeatures[price], lookbackDataDf[price].iloc[-1])
        return np.sqrt(float(temp) / float(prevCount))

    '''
    Computing for Market. By default defers to computeForLookbackData
    '''
    @classmethod
    def computeForMarket(cls, featureParams, featureKey, currentMarketFeatures, instrumentManager):
        score = 0
        scoreDict = instrumentManager.getDataDf()[featureKey]
        scoreKey = 'score'
        if 'instrument_score_feature' in featureParams:
            scoreKey = featureParams['instrument_score_feature']
        if len(scoreDict) < 1:
            return 0
        cumulativeScore = scoreDict.values[-1]
        allInstruments = instrumentManager.getAllInstrumentsByInstrumentId()
        for instrumentId in allInstruments:
            instrument = allInstruments[instrumentId]
            lookbackDataDf = instrument.getDataDf()
            score += instrument.getDataDf()[scoreKey][-1]
        cumulativeScore += score / len(allInstruments)
        return score
