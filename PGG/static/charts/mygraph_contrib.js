function draw_graph(history_contrib, labels){
  labels = labels || {};
  $('#container1').highcharts({
      chart: {
          type: 'line'
      },
      title: {
          text: labels.chart_group_contribution || 'Contribuzione del gruppo al progetto comune'
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
          name: labels.chart_group_series || 'Contribuzione del gruppo',
          color: '#348E03',
          data: history_contrib
      }]
  });
}
