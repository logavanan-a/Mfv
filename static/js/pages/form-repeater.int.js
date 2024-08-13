/*
Template Name: Skote - Admin & Dashboard Template
Author: Themesbrand
Website: https://themesbrand.com/
Contact: themesbrand@gmail.com
File: Form repeater Js File
*/

$(document).ready(function () {
    
    'use strict';

    $('.repeater').repeater({

        show: function () {
            $(this).slideDown()
            var row = $(this).closest('tr')
            var index = $(this).index()
            if (row.prev().find('select') && row.prev().find('select').hasClass('sm_question')) {
                var $options = row.prev().find('select > option').clone()
                $(this).find('select option').remove()
                $(this).find('select').append($options)
            }

            $(this).find('td').each(function () {
                $(this).find('input').removeAttr('readonly', 'readonly')
                $(this).find('input').attr('disabled', false)
                $(this).find('select').attr('disabled', false)
       
                $("[name='group-509["+index+"][352]']").on('click', function() {
                    var date_list = []
                    $('.D_0_0').each(function () {
                        var date_vlu = $(this).val()
                        var index = $(this).index()
                        if(date_vlu){
                            date_list.push({index:date_vlu}) 
                        }
                    })
                    if (date_list.length > 0) {
                        var min_value = date_list[date_list.length - 1].index; // Get the last value in the array
                        var date = new Date(min_value);
                        date.setDate(date.getDate() + 1);
                        var nextDay = date.toISOString().split('T')[0];
                        var index = $(this).closest('.repeater-item').index();
                        $(this).attr('min', nextDay);
                    }
                })
            })
        },
        hide: function (deleteElement) {
            if (confirm('Are you sure you want to delete this form?')) {
                $(this).slideUp(deleteElement);
            }
        },
        ready: function (setIndexes) {}
    });

    
    // window.outerRepeater = $('.outer-repeater').repeater({
    //     defaultValues: {
    //         'text-input': 'outer-default'
    //     },
    //     show: function () {
    //         console.log('outer show');
    //         $(this).slideDown();
    //     },
    //     hide: function (deleteElement) {
    //         console.log('outer delete');
    //         $(this).slideUp(deleteElement);
    //     },
    //     repeaters: [{
    //         selector: '.inner-repeater',
    //         defaultValues: {
    //             'inner-text-input': 'inner-default'
    //         },
    //         show: function () {
    //             console.log('inner show');
    //             $(this).slideDown();
    //         },
    //         hide: function (deleteElement) {
    //             console.log('inner delete');
    //             $(this).slideUp(deleteElement);
    //         }
    //     }]
    // });
    
});

