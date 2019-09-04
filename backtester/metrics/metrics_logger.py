import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
from functools import partial
from pandas.tseries.frequencies import to_offset
from backtester.plotter import generateGraph
from backtester.state_writer import StateWriter
from tensorboardX import SummaryWriter
from datetime import datetime
from backtester.metrics.metrics import Metrics

class MetricsLogger():
	def __init__(self, metrics_to_log_realtime, instrumentManager, priceFeatureKey, startingCapital):
		'''
		Used to create realtime and end of experiment logs. All the data is obtained from Metrics class

		Args:
			metrics_to_log_realtime (dict): contains names of metrics to log realtime corresponding to market and instruments
			rest are explained by their names
			
		'''
		self.metrics_to_log_realtime = metrics_to_log_realtime
		self.instrumentManager = instrumentManager
		self.priceFeatureKey = priceFeatureKey
		self.startingCapital = startingCapital

		self.stateWriter = StateWriter('runLogs', datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S'))
		self.tensorboard_writer = SummaryWriter(logdir='tb_logs\\'+datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S'))

		if self.metrics_to_log_realtime['market'] is not None:
			print('For market, only logging: %s in tensorboard'%self.metrics_to_log_realtime['market'])
		else:
			print('Logging all the available market metrics in tensorboard')
		
		if self.metrics_to_log_realtime['instruments'] is not None:
			print('For instruments, only logging: %s in tensorboard'%self.metrics_to_log_realtime['instruments'])
		else:
			print('Logging all the available instrument metrics in tensorboard')

		

	def get_final_metrics(self, dateBounds):
		allInstruments = self.instrumentManager.getAllInstrumentsByInstrumentId()
		resultDict = {}
		resultDict['instrument_names'] = []
		resultDict['instrument_stats'] = []
		for instrumentId in allInstruments:
			metrics = Metrics(marketFeaturesDf=None)
			metrics.calculateInstrumentFeatureMetrics(instrumentId=instrumentId,
													  priceFeature=self.priceFeatureKey,
													  startingCapital=self.startingCapital,
													  instrumentLookbackData=self.instrumentManager.getLookbackInstrumentFeatures())
			stats = metrics.getMetrics()
			# metricString = metrics.getInstrumentMetricsString()
			resultDict['instrument_names'] += [instrumentId]
			resultDict['instrument_stats'] += [{'total_pnl': stats['Total Pnl(%)'], 'score': stats['Score']}]
			if 'Normalized Score' in stats:
				resultDict['instrument_stats'][-1]['normalized_score'] = stats['Normalized Score']
		metrics = Metrics(marketFeaturesDf=self.instrumentManager.getDataDf())
		metrics.calculateMarketMetrics(None, self.priceFeatureKey, self.startingCapital, dateBounds)
		stats = metrics.getMetrics()
		metricString = metrics.getMarketMetricsString()
		generateGraph(self.instrumentManager.getDataDf(), self.stateWriter.getMarketFeaturesFilename(), metricString, None)
		return resultDict


	def log_tensorboard(self, global_step):
		instrumentIds = self.instrumentManager.getAllInstrumentsByInstrumentId()
		marketFeaturesDf = self.instrumentManager.getDataDf()
		instrumentLookbackData = self.instrumentManager.getLookbackInstrumentFeatures()

		metrics = Metrics(marketFeaturesDf=None)
		startingCapital = self.startingCapital
		
		market_metrics_to_show, instrument_metrics_to_show = self.metrics_to_log_realtime['market'], self.metrics_to_log_realtime['instruments']
		market_stats = metrics.calculateMarketMetricsRealtime(marketFeaturesDf, startingCapital, market_metrics_to_show)
		instrument_stats = metrics.calculateInstrumentFeatureMetricsRealtime(instrumentIds, instrumentLookbackData, startingCapital, instrument_metrics_to_show)

		portfolio_value = marketFeaturesDf['portfolio_value'][-1]  # TODO: find a better way to get this value
		capital = marketFeaturesDf['capital'][-1]  # TODO: find a better way to get this value
		score = marketFeaturesDf['score'][-1]
		self.tensorboard_writer.add_scalars('capital_and_portfolio', {'capital': capital, 'portfolio_value': portfolio_value}, global_step)
		self.tensorboard_writer.add_scalar('score', score, global_step)

		for scalar in market_stats.keys():
			val = market_stats[scalar]
			self.tensorboard_writer.add_scalars('market_features', {scalar: val}, global_step)

		for scalar in instrument_stats.keys():
			self.tensorboard_writer.add_scalars(scalar, instrument_stats[scalar], global_step)

	def saveCurrentState(self, timeOfUpdate):
		self.stateWriter.writeCurrentState(timeOfUpdate, self.instrumentManager)
	

