from django_components import Component, register

@register("table")
class Table(Component):
    def get_context_data(self, title):
        return {
            "title": title,
        }

    # language=HTML
    template= """
    <div class="p-4 bg-white border border-gray-200 rounded-lg shadow-sm dark:border-gray-700 sm:p-6 dark:bg-gray-800">
      <div class="rounded-t-lg py-3 dark:bg-gray-800 dark:text-white px-4">
        <h1 class='flex justify-center text-2xl'>
          {{ title }}
        </h1>
      </div>
      <div class="flex-auto px-0 pt-0 pb-2">
        <div class="block w-full overflow-auto scrolling-touch p-0">
          <table class="min-w-full divide-y divide-gray-200 table-fixed dark:divide-gray-600">
            <thead class="bg-gray-100 dark:bg-gray-700">
              <tr>
                {% slot "header" %}{% endslot %}
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
                {% slot "body" %}{% endslot %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
"""
