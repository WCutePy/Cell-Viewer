from django_components import Component, register


@register("label_matrix_input_fields")
class LabelMatrixInputFieldsComponent(Component):
    def get_context_data(self, matrix_name, row_names, col_names, cell_names):
        return {
            "matrix_name": matrix_name,
            "row_names": row_names,
            "col_names": col_names,
            "cell_names": cell_names,
            "default_rows": ",,,".join(row_names),
            "default_cols": ",,,".join(col_names),
        }
    

    # language=HTML
    template= """
    {% load cellviewer_templatetags %}
    <div class="grid grid-cols-6 gap-6">
        <div class="col-span-6 sm:col-span-3">
            <label for="name" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Annotation name</label>
            <input type="text" name="label-layout-name" maxlength="255" value="{{ matrix_name }}" placeholder="Annotation name" class="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500" id="label-layout-name">
        </div>
    </div>
    
    <div class="grid gap-1 py-6"
        style="grid-template-columns: repeat({{ col_names|length|add:1 }}, minmax(0, 1fr))">
        <div></div>
        {% for col in col_names %}
             <input type="text" name="col" id="col-{{ col }}" maxlength="255" value="{{ col }}"
                    class="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">
        {% endfor %}
    
        {% for row in row_names %}
            <input type="text" name="row" id="row-{{ row }}" maxlength="255" value="{{ row }}"
                    class="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">
            {% for cell in cell_names|at_index_i:forloop.counter0 %}
                <input type="text" name="cell" id="cell-{{ cell }}" maxlength="255" value="{{ cell }}"
                    class="shadow-sm bg-gray-50 border border-gray-300 text-gray-900 sm:text-sm focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500">
            {% endfor %}
            
        {% endfor %}
    </div>
    
    <input type="hidden" name="default-rows" value="{{ default_rows }}">
    <input type="hidden" name="default-cols" value="{{ default_cols }}">
    """
