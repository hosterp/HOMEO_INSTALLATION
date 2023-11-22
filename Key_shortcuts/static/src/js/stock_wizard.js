$(document).on("shown.bs.modal", function () {
setTimeout(function(){
$('.tree_class table').DataTable();
  $('input[type="search"]').focus();
//$('419').DataTable();
}, 2000)
});