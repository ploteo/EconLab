function draw_graph2(history_individ, labels){
  labels = labels || {};
  $('#container2').highcharts({
      chart: {
          type: 'line'
      },
      title: {
          text: labels.chart_individual_contribution || 'La tua contribuzione al progetto comune'
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
          name: labels.chart_individual_series || 'La tua contribuzione',
          color: '#03338E',
          data: history_individ
      }]
  });
}
