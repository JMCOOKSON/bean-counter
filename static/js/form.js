$(document).ready(function() {
  $('#search-form').on('input', function() {
    var searchTerm = $(this).val().toLowerCase();
    if (searchTerm.length > 2) {
      $.ajax({
        url: '/search',
        data: $('#search-term').serialize(),
        type: 'POST',
        success: function(response) {
          console.log('Search term:', searchTerm);
          $('#search-results').empty();
          $.each(response, function(index, item) {
            $('#search-results').append($('<li>').text(item.name));
          });
        }
      });
    } else {
      $('#search-results').empty();
    }
  });
});


