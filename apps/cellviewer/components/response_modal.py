from django_components import Component, register


@register("response_modal")
class ResponseModal(Component):
    """
    A response modal, which can be made to pop on top of the screen
    as a modal should.
    
    This can be used to display any amount of messages to the user.
    It is used by the save function to display multiple responses
    to the screen indicating the success or failure.
    It could be used in more places if needed.
    
    It has a built in response spinner, which will spin until
    the response is loaded inside of the modal.
    
    Important to note, is that this element needs to be put inside of
    a dialog element to function properly.
    It was not possible to have the dialog part be a part of
    this component, and have it function as expected.
    Potentially with more advanced javascript it could be made
    to function "as expected", but currently that is not the case.
    """
    
    def get_context_data(self, title, text):
        return {
            "title": title,
            "text": text
        }

    # language=HTML
    template= """
        <!-- Modal content -->
        <div id="modal-content" class="p-4 bg-white border border-gray-200 rounded-lg shadow-sm dark:border-gray-700 sm:p-6 dark:bg-gray-800">
            <!-- Modal header -->
            <div class="flex items-center justify-between p-4 md:p-5 border-b rounded-t dark:border-gray-600">
                <h1 class="pr-10 text-xl font-semibold text-gray-900 sm:text-2xl dark:text-white">
                    {{ title}}
                </h1>
                <button onclick="this.closest('dialog').close();
                                this.closest('#modal-content').remove();
                                document.getElementById('response_spinner').classList.remove('hidden');"
                                 class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white">
                    <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
                    </svg>
                    <span class="sr-only">Close modal</span>
                </button>
            </div>
            <!-- Modal body -->
            <div class="p-4 text-base font-medium text-gray-900 whitespace-nowrap dark:text-white">
                <div class="text-sm mb-0">
                    {{ text|safe }}
                </div>
            </div>
        </div>
        
                    <script>
                        htmx.onLoad(function(elt){
                            document.getElementById('response_spinner').classList.add("hidden");
                        })
                    </script>
    """
