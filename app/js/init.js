var elem = document.querySelector('#resultModal');
var modal = M.Modal.init(elem);
google.charts.load('current', {
  'packages': ['gauge']
});


function drawChart(value) {
  var chart = new google.visualization.Gauge(document.getElementById('resultMeter'));
  
  var data = google.visualization.arrayToDataTable([
    ['Label', 'Value'],
    ['Rating', 0]
  ]);
  
  var options = {
    width: 200,
    height: 200,
    redFrom: 0,
    redTo: 0.2,
    yellowFrom: 0.2,
    yellowTo: 0.5,
    greenFrom: 0.5,
    greenTo: 1,
    minorTicks: 0,
    majorTicks: ['NONE', 'SOME', 'HIGH'],
    min: 0,
    max: 1,
    animation: {
      duration: 1000,
      easing: 'in'
    }
    
  };
  chart.draw(data, options);
  
  setTimeout(() => {
    data.setValue(0, 1, value);
    chart.draw(data, options);
  }, 300);
}

function showChart() {
  google.charts.setOnLoadCallback(drawChart);
}

$(document).ready(function () {
  var $queryForm = $('#queryForm');
  var results = [];

  var array = [];

  $('#sourceBtn').click(function () {
    if ($('#sourceBtn').text() == 'VIEW SOURCES'){
      $('#sourceList').removeClass('hide');
      $('#sourceBtn').text('HIDE SOURCES');
      var cList = $('#sourceList')
      $.each(array, function (i) {
        var anchor = $('<a/>').text(array[i])
          .addClass('collection-item')
          .attr('href', array[i])
          .attr('target', '_blank')
          .appendTo(cList);
      });
    } else {
      $('#sourceList').addClass('hide');
      $('#sourceBtn').text('VIEW SOURCES');
    }
  });
  $queryForm.on('submit', function (e) {
    e.preventDefault();
    $('.progress').removeClass('hide');
    var query = $queryForm.find('#query').val();
    $.ajax({
      url: '/query',
      method: 'POST',
      data: {
        data: query
      },  
      dataType: 'json',
      success: function (response) {
        array = [];
        $('.progress').addClass('hide');
        modal.open();
        var value = 0;
        if (response.data.HIGH.length){
          value = 1;
        } else if ((response.data.SOME.length)){
          value = 0.5;
        }
        var hrefs = response.data.href;
        hrefs = hrefs.filter(function (item, pos) {
          return hrefs.indexOf(item) === pos;
        });

        drawChart(value);
        $("#resultQuery").text(query);
        
        if(response.data.HIGH.length) {
          $('#sourceBtn').show();
          $("#resultQueryGenuine").text('There are high chances for your content to be coming from other online sources.');
          hrefs.map( function (href){
            response.data.HIGH.map(function (url) {
              if(href.indexOf(url)>-1){
                array.push(href);
              }
            })
          })
        } else if (response.data.SOME.length) {
          $('#sourceBtn').show();
          $("#resultQueryGenuine").text('There are some chances for your content to be coming from other online sources.');
          hrefs.map(function (href) {
            response.data.SOME.map(function (url) {
              if (href.indexOf(url) > -1) {
                array.push(href);
              }
            })
          })
        } else {
          $('#sourceBtn').hide();
          $("#resultQueryGenuine").text('No online sources found for your content.');
        }
      },
      error: function (error) {
        $('.progress').addClass('hide');
        console.log();
      }
    })

  })

});