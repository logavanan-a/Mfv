function onSelectChange(){
    var sel = document.getElementById('select_box');
    var opt = sel.options[sel.selectedIndex].text;

    if(opt === 'Yes'){ 
        document.getElementById('reason_skip').style.display = "none";
        document.getElementById("reason_select").selectedIndex = 0;
        document.getElementById('reason_select').removeAttribute('required','required');
    }
    else if(opt === 'No'){ 
        document.getElementById('reason_skip').style.display = 'block';
        document.getElementById('reason_select').setAttribute('required','required');
    }
   
}


function activateFunction() {
    var hidden_child_talk=document.getElementById('hidden_child_talk');
    if(hidden_child_talk.value == "0"){
        document.getElementById('reason_skip').style.display = 'block';
    }
    
}

function onSelectChange_siblings(val){
    // var sel = document.getElementById('siblings');
    // var opt = sel.options[sel.selectedIndex].text;
    
    if(val.checked){ 
        document.getElementById('siblings_details').style.display = "block";
        document.getElementById('siblings_details_field').setAttribute('required','required');

    }
    else{ 
        document.getElementById('siblings_details').style.display = 'none';
        document.getElementById('siblings_details_field').removeAttribute('required','required');
        document.getElementById('siblings_details_field').value='';

    }
   
}

function onSelectChange_cwc_type(){
    var sel = document.getElementById('cwc_remark_type');
    var opt = sel.options[sel.selectedIndex].text;

    if(opt === 'Other'){ 
        document.getElementById('cwc_remark').setAttribute('required','required');
        document.querySelector('#cwc_remark_label').innerHTML = 'CWC Remark <span class="required-field"></span>'; 
    }
    else{ 
        document.getElementById('cwc_remark').removeAttribute('required','required');
        document.querySelector('#cwc_remark_label').innerHTML = 'CWC Remark </span>'; 
    }
   
}

// function onSelectChange_saa(){
//     var sel = document.getElementById('link_to_saa');
//     var opt = sel.options[sel.selectedIndex].text;

//     if(opt === 'Yes'){ 
//         document.getElementById('saa_details').style.display = "block";
//         document.getElementById('saa_detail').setAttribute('required','required');

//     }
//     else if(opt === 'No'){ 
//         document.getElementById('saa_details').style.display = 'none';
//         document.getElementById('saa_detail').removeAttribute('required','required');
//     }
   
// }
//function for get the code of questions based on question type
function name_return_fun(type, group = null) {
    if (group == 'inline') {
        if (type.is("select")) {
            return 'S'
        } else if (type.is("input")) {
            if (type.attr('type') == 'text') {
                return 'T'
            } else if (type.attr('type') == 'date' || type.attr('type') == 'month') {
                return 'D'
            } else if (type.attr('type') == 'checkbox') {
                return 'C'
            } else if (type.attr('type') == 'number') {
                return 'T'
            }
        }
    } else {
        if (type.is("select")) {
            return 'S_0_0'
        } else if (type.is("input")) {
            if (type.attr('type') == 'text') {
                return 'T_0_0'
            } else if (type.attr('type') == 'date' || type.attr('type') == 'month') {
                return 'D_0_0'
            } else if (type.attr('type') == 'checkbox') {
                return 'C_0_0'
            } else if (type.attr('type') == 'number') {
                return 'T_0_0'
            } else if (type.attr('type') == 'hidden') {
                return 'H_0_0'
            }
        }
    }
}


function enableDateField(field) {
    if (field.type == "text") {
        var dateValue = $(field).val();
        var dateArray = dateValue.split('-');
        var year = parseInt(dateArray[2], 10);
        var month = String(parseInt(dateArray[1], 10)).padStart(2, '0');
        var day = String(parseInt(dateArray[0], 10)).padStart(2, '0');
        // Create a new Date object with the selected date
        // var selectedDate = new Date(year, month - 1, day);
        // Set the input type to "date"
        field.type = "date";

        // Set the value of the date field to the selected date
        field.value = year + "-" + month + "-" + day;
    }
}

function formating_main_questions(questions, main_ans) {
    $(questions).each(function () {
        inner_ans = {}
        if ($(this).is(':checkbox')) {
            values = Array.from(document.querySelectorAll('input[id="' + $(this).attr('id') + '"][type="checkbox"]')).filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value)
            inner_ans[name_return_fun($(this))] = JSON.stringify(values.map(Number))
        }else if ($(this).is(':radio')) {
            inner_ans[name_return_fun($(this))] = $('input[name="'+ $(this).attr('name') +'"]:checked').val()
        } else if (($(this).attr('type') == 'date' || $(this).attr('type') == 'month') && $.trim($(this).val()) != '') {
            var dateObj = new Date($.trim($(this).val()));
            var day = dateObj.getDate();
            var month = dateObj.getMonth() + 1;
            var year = dateObj.getFullYear();
            if ($(this).attr('type') == 'month') {
                var formattedDate = month + '-' + year
            } else {
                var formattedDate = day + '-' + month + '-' + year
            }
            inner_ans[name_return_fun($(this))] = formattedDate
        } else if ($(this).is("select") && $(this).prop('multiple')) {
            inner_ans[name_return_fun($(this))] = JSON.stringify($(this).val().map(Number))
        } else if ($(this).is("select")) {
            inner_ans[name_return_fun($(this))] = $('#' + $(this).attr('id') + ' option:selected').val()
        } else {
            inner_ans[name_return_fun($(this))] = $.trim($(this).val())
        }
        main_ans[$(this).attr('id')] = [inner_ans]
    })
    return main_ans
}

function makeRequired(){
    var sel = document.getElementById('reason_select');
    var opt = sel.options[sel.selectedIndex].text;
    if(opt === 'Other'){ 
        document.getElementById('remarks').setAttribute('required','required');
        document.querySelector('#reason_label').innerHTML = 'Remarks<span class="required-field"></span>'; 
    }
    else{ 
        document.getElementById('remarks').removeAttribute('required','required');
        document.querySelector('#reason_label').innerHTML = 'Remarks'; 


   }
}
function makeReasonRequired(){
    var file = document.getElementById('photo_with_child');
    if(file.files.length == 0){ 
        document.getElementById('reason_for_not_upload').setAttribute('required','required');
        document.querySelector('#photo_reason_label').innerHTML = 'Reason<span class="required-field"></span>'; 
    }
    else{ 
        document.getElementById('reason_for_not_upload').removeAttribute('required','required');
        document.querySelector('#photo_reason_label').innerHTML = 'Reason'; 


   }
}
function manually_unflag_toggle(){
    var manually_unflaged=document.getElementById('manually_unflaged');
    if(manually_unflaged.checked == true){
        document.getElementById('manually_activate1').style.display = 'block';
        document.getElementById('manually_activate2').style.display = 'block';
        document.getElementById('manuallu_unflag_till_date').setAttribute('required','required');
        document.querySelector('#manuallu_unflag_till_date_label').innerHTML = 'Manually unflagged till date<span class="required-field"></span>'; 
        document.getElementById('manually_unflag_remark').setAttribute('required','required');
        document.querySelector('#manually_unflag_remark_label').innerHTML = 'Reason to manually unflag child<span class="required-field"></span>'; 


    }else{
        document.getElementById('manually_activate1').style.display = 'none';
        document.getElementById('manually_activate2').style.display = 'none';
        document.getElementById('manuallu_unflag_till_date').removeAttribute('required','required');
        document.querySelector('#manuallu_unflag_till_date_label').innerHTML = 'Manually unflagged till date'; 
        document.getElementById('manually_unflag_remark').removeAttribute('required','required');
        document.querySelector('#manually_unflag_remark_label').innerHTML = 'Reason to manually unflag child'; 
        document.getElementById('manuallu_unflag_till_date').value=''
        document.getElementById('manually_unflag_remark').value=''
    }

}

function manually_unflag_required(){
    var manually_unflaged=document.getElementById('manually_unflaged');
    if(manually_unflaged.checked == true){
        document.getElementById('manuallu_unflag_till_date').setAttribute('required','required');
        document.querySelector('#manuallu_unflag_till_date_label').innerHTML = 'Manually unflagged till date<span class="required-field"></span>'; 
        document.getElementById('manually_unflag_remark').setAttribute('required','required');
        document.querySelector('#manually_unflag_remark_label').innerHTML = 'Reason to manually unflag child<span class="required-field"></span>'; 

    }else{
        document.getElementById('manuallu_unflag_till_date').removeAttribute('required','required');
        document.getElementById('manuallu_unflag_till_date').value=''
        document.querySelector('#manuallu_unflag_till_date_label').innerHTML = 'Manually unflagged till date'; 
        document.getElementById('manually_unflag_remark').removeAttribute('required','required');
        document.getElementById('manually_unflag_remark').value=''
        document.querySelector('#manually_unflag_remark_label').innerHTML = 'Reason to manually unflag child'; 

    }
}

$(function(){

    var dtToday = new Date();

    var month = dtToday.getMonth() + 1;
    var day = dtToday.getDate();
    var year = dtToday.getFullYear();

    if(month < 10)
        month = '0' + month.toString();
    if(day < 10)
        day = '0' + day.toString();

    var maxDate = year + '-' + month + '-' + day;    
    $('#date_of_call').attr('max', maxDate);
    $('#date_of_birth').attr('max', maxDate);
    $('#date_of_visit').attr('max', maxDate);
    $('#date_of_admission').attr('max', maxDate);
    $('#document_date').attr('max', maxDate);
    $('#last_date_of_cwc_order_or_review').attr('max', maxDate);
    $('#manuallu_unflag_till_date').attr('min', maxDate);
    $('#caring_registration_date').attr('max', maxDate);
    $('#date_of_exit').attr('max', maxDate);
    $('#old_shelter_date_of_exit').attr('max', maxDate);
    

    // var tday = dtToday.getDate()+1;
    // if(tday < 10)
    //     tday = '0' + tday.toString();

    // var minDate = year + '-' + month + '-' + tday;
    // $('#date_of_exit').attr('max', minDate);
    // $('#date_of_exit').attr('min', maxDate);
    // $('#admission_date').attr('max', minDate);
    // $('#admission_date').attr('min', maxDate);


});
// function dateCheck(){
//     // var admission_date = document.getElementById('admission_date');
//     // var date_of_exit = document.getElementById('date_of_exit')
//     var old_admission_date = document.getElementById("old_admission_date").value;
//     date_of_exit.setAttribute("min", old_admission_date);
//     // admission_date.setAttribute("min", old_admission_date);

//     // admission_date.setAttribute("max", date_of_exit);
// }

function date_of_birth_validations(value){

    $('#date_of_admission').attr('min', value);
    $('#last_date_of_cwc_order_or_review').attr('min', value);
    $('#carings_document_uploaded_date').attr('min', value);
    $('#manually_unflaged_till_date').attr('min', value);
    
    
}


// function dateCheck1() {
//     var date_of_exit = document.getElementById('date_of_exit');
//     var admission_date = document.getElementById('admission_date');
//     if (date_of_exit.value > admission_date.value){
//         admission_date.style.borderColor='red';
//         admission_date.value=''
//         document.getElementById('date_error').innerText='Admission date should be greater than exit date'

//     }else{
//         admission_date.style.borderColor='#ced4da';
//         document.getElementById('date_error').innerText=''

//     } 
// }
// function dateCheck2() {
//     var admission_date = document.getElementById('old_admission_date');
//     var date_of_exit = document.getElementById('date_of_exit')

//     if (date_of_exit.value <= admission_date.value){
//         date_of_exit.style.borderColor='red';
//         date_of_exit.value=''
//         document.getElementById('date_error2').innerText='Please enter valid exit date and exit date'

//     }else{
//         date_of_exit.style.borderColor='#ced4da';
//         document.getElementById('date_error2').innerText=''

//     }
// }

function validate2(el) {
    warningel   = document.getElementById( 'element' );
    var allowedExtensions =  /(\.jpg|\.png|\.jpeg)$/i; 

    if (!allowedExtensions.exec(el.value)) { 
        warningel.innerHTML = "File type not allowed";
        el.value = ''; 
        el.classList.add("border", "border-danger");
        return false; 
    }
}

function validate(el) {
    var image_size = document.getElementById('image_size');
    var maxfilesize = parseInt(image_size.value) * 1024 * 1024,  
    filesize    = el.files[0].size,
    warningel   = document.getElementById( 'element' );
     
    if ( filesize > maxfilesize )
    {
      warningel.innerHTML = "Selected file is too large"
      el.value=''
      el.classList.add("border", "border-danger");
      return false;
    }
    else
    {
      warningel.innerHTML = '';
      el.classList.remove("border", "border-danger");
      return true;
    }  
    
  }
  function toggle(source) {
    checkboxes = document.querySelectorAll('.select,.selectFalse');
    for(var i=0, n=checkboxes.length;i<n;i++) {
      checkboxes[i].checked = source.checked;
    }
  }


// function seemore_toggle(){
//     var seemore = document.getElementById('seemore');
//     if (seemore.innerText == 'See More'){
//         seemore.innerText='See Less'
//     }
//     else{
//         seemore.innerText='See More'
//     }

// }

function caring_required(val1,val2){
   
    if (val1 != '' || val2 != ''){
        // document.getElementById('caring_date_label').innerHTML='Caring Registration Date <span class="required-field"></span>';
        document.getElementById('caring_number_label').innerHTML='Caring Registration Number <span class="required-field"></span>';
        // document.getElementById('caring_registration_date').setAttribute('required','required');
        document.getElementById('caring_registration_number').setAttribute('required','required');
    }
    else{
        // document.getElementById('caring_date_label').innerHTML='Caring Registration Date';
        document.getElementById('caring_number_label').innerHTML='Caring Registration Number';
        // document.getElementById('caring_registration_date').removeAttribute('required','required');
        document.getElementById('caring_registration_number').removeAttribute('required','required');
    
    }
}

function filter_function() {
    var start_date = document.getElementById("start_date").value;
    document.getElementById("end_date").setAttribute("min", start_date);
    
  }

function onSelect_transfer_type(){
    var sel = document.getElementById('transfer_type');
    var opt = sel.options[sel.selectedIndex].text;

    if(opt === 'Transfer'){ 
        document.getElementById('newshelterhome').style.display = "block";
        document.getElementById('exit_remark_field').style.display = "none";
        document.getElementById('exit_remark').removeAttribute('required','required');
        document.getElementById('state').setAttribute('required','required');
        document.getElementById('district').setAttribute('required','required');
        document.getElementById('new_shelter_home_name').setAttribute('required','required');
        document.getElementById('admission_date').setAttribute('required','required');


        
    }
    else if(opt === 'Exit'){ 
        document.getElementById('newshelterhome').style.display = "none";
        document.getElementById('exit_remark_field').style.display = "block";
        document.getElementById('exit_remark').setAttribute('required','required');
        document.getElementById('state').removeAttribute('required','required');
        document.getElementById('district').removeAttribute('required','required');
        document.getElementById('new_shelter_home_name').removeAttribute('required','required');
        document.getElementById('admission_date').removeAttribute('required','required');
    }
   
}

function old_shelter_home(val){
    $('#old_shelter_date_of_exit').attr('min', val.value);
}
function for_admission_date(val){
    $('#admission_date').attr('min', val.value);
}

function start_date_required(val){

    if (val.checked){
        document.getElementById('start_date_label').innerHTML='Case Start Date <span class="required-field"></span>';
        document.getElementById('start_date').setAttribute('required','required');
    }else{
        document.getElementById('start_date_label').innerHTML='Case Start Date ';
        document.getElementById('start_date').removeAttribute('required','required');
    }
}
function reason_for_pause_required(pause_date){
    if (pause_date.value!=''){
        document.getElementById('reason_for_pause').setAttribute('required','required');
        document.getElementById('reason_for_pause_label1').innerHTML='Reasons for Pausing the Child`s Case <span class="required-field"></span>';
        document.getElementById('reason_for_pause_label2').innerHTML='Reasons for Pausing the Child`s Case <span class="required-field"></span>';

    }else{
        document.getElementById('reason_for_pause').removeAttribute('required','required');
        document.getElementById('reason_for_pause_label1').innerHTML="Reasons for Pausing the Child's Case ";
        document.getElementById('reason_for_pause_label2').innerHTML="Reasons for Pausing the Child's Case ";

    }
}

function reason_for_end_required(end_date){
    if (end_date.value!=''){
        document.getElementById('reason_for_end').setAttribute('required','required');
        document.getElementById('reason_for_end_label1').innerHTML='Reasons for Ending the Child`s Case <span class="required-field"></span>';
        document.getElementById('reason_for_end_label2').innerHTML='Reasons for Ending the Child`s Case <span class="required-field"></span>';

    }else{
        document.getElementById('reason_for_end').removeAttribute('required','required');
        document.getElementById('reason_for_end_label1').innerHTML="Reasons for Ending the Child's Case ";
        document.getElementById('reason_for_end_label2').innerHTML="Reasons for Ending the Child's Case ";

    }
}

function onSelectChange_reason_pause(reason_for_pause){
    var opt = reason_for_pause.options[reason_for_pause.selectedIndex].text;

    if(opt === 'Other'){ 
        document.getElementById('remark_for_pause_skip').style.display = "block";
        document.getElementById('remark_for_pause').setAttribute('required','required');
    }else{ 
        document.getElementById('remark_for_pause_skip').style.display = 'none';
        document.getElementById('remark_for_pause').removeAttribute('required','required');
    }
   
}
function onSelectChange_reason_end(reason_for_end){
    var opt = reason_for_end.options[reason_for_end.selectedIndex].text;

    if(opt === 'Other'){ 
        document.getElementById('remark_for_end_skip').style.display = "block";
        document.getElementById('remark_for_end').setAttribute('required','required');
    }else{ 
        document.getElementById('remark_for_end_skip').style.display = 'none';
        document.getElementById('remark_for_end').removeAttribute('required','required');
    }
   
}
function adoptioneligibility_checkbox(val){
    if (val.value!=''){
        document.getElementById('worked_for_adoption_eligibility').checked=false;
    }else{
        document.getElementById('worked_for_adoption_eligibility').checked=true;
    }
}

function password_checking(pass1,pass2){
    if (pass1.value!=pass2.value){
        document.getElementById('confirm_password').innerHTML='Password do not match.';
    }else{
        document.getElementById('confirm_password').innerHTML='Please enter the valid confirm password.';
    }
}

$("#boundary_1").on("change", function (event) {
    var optionSelected = $(this).find("option:selected");
    var valueSelected = optionSelected.attr('value');
    adres_widget_1(valueSelected)
});


//ajax call for get the locations
function adres_widget_1(parent_valueSelected, selected = null) {
    var next_dropdown_boundry = 'boundary_2'
    var survey_id = $('#__survey_id').val();
    data = {
        'selected_boundry': parent_valueSelected,
        'survey_id': survey_id,
        'transfer_page': $('#transfer_page').val()
    };
    $.ajax({
        type: "GET",
        url: '/configuration/ajax/get_location/',
        data: data,
        success: function (result) {
            $("#" + next_dropdown_boundry + " option").remove();
            $("#facility option").remove();
            
            result = JSON.parse(result)
            ans = result['result_set']
            if (ans[ans.length - 1]) {
                a = '<option selected value="" > </option>';
                $("#" + next_dropdown_boundry).append(a);
            }
            if (ans == 0) {
                $("#" + next_dropdown_boundry + " option").remove();
                a =
                    '<option selected  value=""> </option>';
                $("#" + next_dropdown_boundry).append(a);
            } else {
                $.each(ans, function (key, value) {
                    if (typeof value['id'] !== "undefined") {
                        if (parseInt(selected) == value['id'] || ans.length == 1) {
                            a = '<option value=' + value['id'] + ' selected>' +
                                value['name'] + '</option>';
                            $("#" + next_dropdown_boundry).append(a);
                            $("#" + next_dropdown_boundry).trigger('change')
                        } else {
                            a = '<option value=' + value['id'] + '>' +
                                value['name'] + '</option>';
                            $("#" + next_dropdown_boundry).append(a);
                        }
                    }
                })

                project_id = result['project_ids']

                unhideOptions('project_id'); // Unhide options
                hideOptions(project_id,'project_id');
            }
        }
    })
}

// Store and remove options to "hide" them
function hideOptions(visibleIds,hide_id,select2=true) {
    const select = $("#"+hide_id);

    // Store all options in a data attribute before hiding
    if (!select.data("hiddenOptions")) {
        select.data("hiddenOptions", select.html()); // Store original options once
    }

    // Remove all options that are NOT in the visibleIds list
    select.find("option").each(function() {
        const optionValue = parseInt($(this).val(), 10);
        if (!visibleIds.includes(optionValue)) {
            $(this).remove();
        }
    });
    if(select2){
        // Refresh select2 to reflect changes
        select.select2();
    }
}

// Restore options to "unhide" them
function unhideOptions(hide_id,select2=true) {
    const select = $("#"+hide_id);
    select.html(select.data("hiddenOptions")); // Restore saved options
    if(select2){
        select.select2(); // Refresh select2
    }
}

function disable_edit_fields() {
    $('#survey input').attr('readonly', 'readonly');
    $('#survey input[type=checkbox]').attr("disabled", "disabled");
    $('#survey input[type=button]').attr("disabled", "disabled")
    $('#survey select').attr('disabled', true);
    $('#submitting').attr('disabled', true);
}


// On menu button click, open SweetAlert with a date input
$('.change_activity_date').on('click', function() {
    const today = new Date().toISOString().split('T')[0];

    // Get the last activity date from the data attribute
    const lastActivityDate = $(this).data('last-activity') || '';

    Swal.fire({
        title: 'Enter Activity Date',
        html: `
            <input type="date" id="activity-date" class="swal2-input" max="${today}" value="${lastActivityDate}" placeholder="Activity Date">
        `,
        showCancelButton: true,
        confirmButtonText: 'Save',
        cancelButtonText: 'Cancel',
        preConfirm: () => {
            const activityDate = document.getElementById('activity-date').value;
            if (!activityDate) {
                Swal.showValidationMessage('Please enter a date');
            }
            return activityDate;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const activityDate = result.value;
            saveActivityDate(activityDate);
        }
    });
});

// AJAX function to save the activity date
function saveActivityDate(activityDate) {
    $.ajax({
        url: '/application_master/save-activity/',  // Django URL to save the activity
        method: 'POST',
        data: {
            'activity_date': activityDate,
        },
        success: function(response) {
            Swal.fire({
                title: 'Success!',
                text: 'Activity date saved successfully.',
                icon: 'success',
                confirmButtonText: 'OK'
            }).then((result) => {
                location.reload();
            });
        },
        error: function(error) {
            Swal.fire({
                title: 'Error!',
                text: 'Failed to save activity date.',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        }
    });
}