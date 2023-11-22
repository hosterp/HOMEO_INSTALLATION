openerp.web_menu = function (jQuery) {
    $(document).bind('keydown', 'f2', function assets() {
        window.location.href = window.location.protocol + '//' + window.location.host + '/' + 'web?debug=1#view_type=form&model=account.invoice&menu_id=441&action=395';
    setTimeout(function(){
    $('button.oe_button.oe_form_button_create').click();
}, 4000)
    });

};