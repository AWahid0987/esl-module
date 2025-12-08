/** @odoo-module **/

// Use plain JavaScript/jQuery for portal - more reliable
(function() {
    'use strict';

    // Wait for DOM and jQuery to be ready
    function initAttendance() {
        if (typeof jQuery === 'undefined') {
            setTimeout(initAttendance, 100);
            return;
        }

        var $ = jQuery;
        
        // Initialize buttons when page loads
        function initializeAttendanceButtons() {
            // Remove any existing handlers to avoid duplicates
            $('#check_in_btn').off('click').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var $btn = $(this);
                console.log('Check In button clicked');
                if (!$btn.prop('disabled')) {
                    // Get commit value - REQUIRED for check in
                    var commit = $('#checkin_commit').val() ? $('#checkin_commit').val().trim() : '';
                    
                    // Validate commit is required before check in
                    if (!$('#checkin_commit_div').is(':hidden') && !commit) {
                        alert('Please enter a commit message before checking in. Commit is required.');
                        $('#checkin_commit').focus();
                        $('#checkin_commit').css('border-color', 'red');
                        return;
                    }
                    
                    // Reset border color if commit is provided
                    $('#checkin_commit').css('border-color', '');
                    
                    // Start location capture
                    performAttendanceAction('check_in', $btn, commit);
                } else {
                    alert('Check In is disabled. You are already checked in.');
                }
            });

            $('#check_out_btn').off('click').on('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var $btn = $(this);
                console.log('Check Out button clicked');
                if (!$btn.prop('disabled')) {
                    // Get commit value (optional - location is priority)
                    var commit = $('#checkout_commit').val() ? $('#checkout_commit').val().trim() : '';
                    // Start location capture immediately - commit is optional
                    performAttendanceAction('check_out', $btn, commit);
                } else {
                    alert('Check Out is disabled. Please check in first.');
                }
            });
            
            // Show/hide commit fields based on attendance state
            if ($('#check_in_btn').prop('disabled')) {
                $('#checkout_commit_div').show();
            }

            // Make sure buttons are visible and clickable
            $('#check_in_btn, #check_out_btn').show().css('cursor', 'pointer');
            
            console.log('Attendance buttons initialized');
        }

        // Initialize immediately if DOM is ready
        if (document.readyState === 'loading') {
            $(document).ready(function() {
                setTimeout(initializeAttendanceButtons, 300);
            });
        } else {
            setTimeout(initializeAttendanceButtons, 300);
        }
    }

    // Start initialization
    initAttendance();

    function performAttendanceAction(action, $btn, commit) {
        var $ = jQuery;
        
        // Disable button during processing
        $btn.prop('disabled', true);
        
        // Show location status
        var $status = $('#location_status');
        $status.show().removeClass('alert-danger alert-success').addClass('alert-warning')
            .html('<i class="fa fa-map-marker me-2"/>Getting your location...');
        
        console.log('Requesting geolocation for', action);
        
        // Get geolocation - simple and working (same as backend)
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    var latitude = position.coords.latitude;
                    var longitude = position.coords.longitude;
                    var accuracy = position.coords.accuracy;
                    
                    console.log('Location captured:', latitude, longitude, 'Accuracy:', accuracy, 'meters');
                    
                    // Validate coordinates
                    if (!latitude || !longitude || isNaN(latitude) || isNaN(longitude)) {
                        $status
                            .removeClass('alert-warning')
                            .addClass('alert-danger')
                            .html('<i class="fa fa-exclamation-triangle me-2"/>Invalid location received. Please try again.');
                        $btn.prop('disabled', false);
                        return;
                    }
                    
                    // Use coordinates directly (same as backend - no rounding that might affect accuracy)
                    // Backend code doesn't round, so we also use raw coordinates for 100% accuracy
                    console.log('Sending coordinates to server:', latitude, longitude);
                    
                    // Update status
                    $status.html('<i class="fa fa-check-circle me-2"/>Location captured successfully!');
                    
                    // Call check in/out with commit (send raw coordinates for 100% accuracy)
                    callAttendanceAPI(latitude, longitude, $btn, $status, commit);
                },
                function (error) {
                    console.error('Geolocation error:', error);
                    // Handle geolocation errors
                    var errorMsg = 'Unable to get your location. ';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            errorMsg += 'Please allow location access in browser settings.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMsg += 'Location information unavailable. Please ensure GPS is enabled.';
                            break;
                        case error.TIMEOUT:
                            errorMsg += 'Location request timeout. Please try again.';
                            break;
                        default:
                            errorMsg += 'An unknown error occurred.';
                            break;
                    }
                    
                    $status
                        .removeClass('alert-warning')
                        .addClass('alert-danger')
                        .html('<i class="fa fa-exclamation-triangle me-2"/>' + errorMsg);
                    
                    $btn.prop('disabled', false);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 30000,
                    maximumAge: 0
                }
            );
        } else {
            // Geolocation not supported
            $status
                .removeClass('alert-warning')
                .addClass('alert-danger')
                .html('<i class="fa fa-exclamation-triangle me-2"/>Geolocation is not supported by your browser.');
            
            $btn.prop('disabled', false);
        }
    }

    function callAttendanceAPI(latitude, longitude, $btn, $status, commit) {
        var $ = jQuery;
        $status.html('<i class="fa fa-spinner fa-spin me-2"/>Processing attendance...');
        
        // Use jQuery AJAX for portal (more reliable)
        $.ajax({
            url: '/my/attendance/check_in_out',
            type: 'POST',
            dataType: 'json',
            contentType: 'application/json',
            data: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    latitude: latitude,
                    longitude: longitude,
                    commit: commit || '',
                },
                id: Math.floor(Math.random() * 1000000000),
            }),
            headers: {
                'Content-Type': 'application/json',
            },
        }).done(function (response) {
            // Handle JSON-RPC response
            var result = response.result || response;
            
            console.log('Attendance API response:', result);
            
            if (result.error) {
                $status
                    .removeClass('alert-warning')
                    .addClass('alert-danger')
                    .html('<i class="fa fa-exclamation-triangle me-2"/>' + result.error);
                $btn.prop('disabled', false);
            } else if (result.success) {
                $status
                    .removeClass('alert-warning alert-danger')
                    .addClass('alert-success')
                    .html('<i class="fa fa-check-circle me-2"/>' + result.message + ' Location: ' + (result.checkin_address || result.checkout_address || 'Saved'));
                
                // Reload page after 2 seconds to show updated state
                setTimeout(function () {
                    window.location.reload();
                }, 2000);
            } else {
                $status
                    .removeClass('alert-warning')
                    .addClass('alert-danger')
                    .html('<i class="fa fa-exclamation-triangle me-2"/>Unexpected response from server');
                $btn.prop('disabled', false);
            }
        }).fail(function (xhr, status, error) {
            console.error('Attendance API error:', xhr, status, error);
            var errorMsg = 'Error: ';
            if (xhr.responseJSON && xhr.responseJSON.error) {
                errorMsg += xhr.responseJSON.error;
            } else if (xhr.responseJSON && xhr.responseJSON.result && xhr.responseJSON.result.error) {
                errorMsg += xhr.responseJSON.result.error;
            } else {
                errorMsg += (error || 'Unknown error occurred');
            }
            
            $status
                .removeClass('alert-warning')
                .addClass('alert-danger')
                .html('<i class="fa fa-exclamation-triangle me-2"/>' + errorMsg);
            $btn.prop('disabled', false);
        });
    }
})();

