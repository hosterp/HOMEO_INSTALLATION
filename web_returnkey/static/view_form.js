openerp.web_returnkey = function(instance) {

    /**
     * Set focus to the next visible input field, select value if not "textarea"
     * Credits to: http://stackoverflow.com/a/292005
     *
     * @param {Object} input
     */
    var go_next = function (input) {
        $(':input:visible:eq(' + ($(':input:visible').index(input) + 1) + ')').focus().not('textarea').select()
    };

    var keypress = function (e) {
        if (e.which === $.ui.keyCode.ENTER && !e.shiftKey) {
            e.preventDefault();
            go_next(e.target);
        }
    }

    instance.web.FormView.include({
        start: function() {
            this.$el.keypress(keypress);
            return this._super.apply(this,arguments);
        }
    });

    instance.web.form.FieldSelection.include({
        initialize_content: function() {
            this.$("select").keypress(keypress);
            return this._super.apply(this,arguments);
        }
    });

    instance.web.form.FieldText.include({
        initialize_content: function() {
            this.$("textarea").keypress(keypress);
            return this._super.apply(this,arguments);
        }
    });
    

    instance.web.form.FieldMany2ManyTags.include({
        initialize_content: function() {
            var self = this;
            this.$("textarea").keydown(function(e) {
                if (e.which === $.ui.keyCode.TAB && self._drop_shown) {
                    self.$text.textext()[0].autocomplete().selectFromDropdown();

                }
                if (e.which === $.ui.keyCode.ENTER && !self._drop_shown) {
                    go_next(e.target);
                }
            });
            return this._super.apply(this,arguments);
        }
    });

    instance.web.ListView.include({
            keypress_ENTER: function(e) {
                return this.keydown_TAB(e);
            }
    });

};