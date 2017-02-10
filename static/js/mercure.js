$(document).ready(function() {
    $datahref = $('tr[data-href]');
    $datahref.click(function() {
       window.document.location = $(this).data('href');
    });
    $datahref.hover(function() {
        $(this).css('cursor', 'pointer');
    });
});