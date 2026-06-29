function draw_graph3(history_payoff, labels){
  labels = labels || {};
  $('#container3').highcharts({
      chart: {
          type: 'line'
      },
      title: {
          text: labels.chart_payoffs || 'I tuoi guadagni totali'
      },
      xAxis: {
        allowDecimals: false,
           title: {
              text: labels.round || 'Round'
          },
         accessibility: {
            rangeDescription: 'Range: 1 to 20'
        }
      },
      yAxis: {
          title: {
              text: labels.chart_y_points || 'Punti'
          }
      },
        plotOptions: {
        series: {
            label: {
                connectorAllowed: false
            },
            pointStart: 1
        }
    },
      series: [{
          name: labels.chart_payoffs_series || 'I tuoi guadagni totali',
          color: '#9A0900',
          data: history_payoff
      }]
  });
}
