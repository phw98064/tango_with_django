from django.shortcuts import render
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.http import HttpResponse

def about(request):
    # 构建一个字典，作为上下文传给模板引擎
    # 注意，boldmessage 键对应于模板中的 {{ boldmessage }}
    #context_dict = {'boldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}

    # 返回一个渲染后的响应发给客户端
    # 为了方便，我们使用的是 render 函数的简短形式
    # 注意，第二个参数是我们想使用的模板
    return render(request, 'rango/about.html')

def index(request):
    # 构建一个字典，作为上下文传给模板引擎
    # 注意，boldmessage 键对应于模板中的 {{ boldmessage }}
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list
    # 返回一个渲染后的响应发给客户端
    # 为了方便，我们使用的是 render 函数的简短形式
    # 注意，第二个参数是我们想使用的模板
    return render(request, 'rango/index.html', context=context_dict)

def show_category(request, category_name_slug):
    # Create a context dictionary which we can pass
    # to the template rendering engine.
    context_dict = {}
    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # The .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        # Retrieve all of the associated pages.
        # The filter() will return a list of page objects or an empty list.
        pages = Page.objects.filter(category=category)
        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from
        # the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything -
        # the template will display the "no category" message for us.
        context_dict['category'] = None
        context_dict['pages'] = None
    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context=context_dict)
@login_required
def add_category(request):
    form = CategoryForm()
    # A HTTP POST?

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)
            # Now that the category is saved, we could confirm this.
            # For now, just redirect the user back to the index view.
            return redirect(reverse('rango:index'))
        else:
            # The supplied form contained errors -
            # just print them to the terminal.
            print(form.errors)
    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    if category is None:
        return redirect(reverse('rango:index'))

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category', kwargs={'category_name_slug': category_name_slug}))
        else:
            print(form.errors)

    context_dict = {'form':form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


def register(request):
    # 一个布尔值，告诉模板注册是否成功
    # 一开始设为 False，注册成功后改为 True
    registered = False

    # 如果是 HTTP POST 请求，处理表单数据
    if request.method == 'POST':
        # 尝试获取原始表单数据
        # 注意，UserForm 和 UserProfileForm 中的数据都需要
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # 如果两个表单中的数据是有效的……
        if user_form.is_valid() and profile_form.is_valid():
            # 把 UserForm 中的数据存入数据库
            user = user_form.save()

            # 使用 set_password 方法计算密码哈希值
            # 然后更新 user 对象
            user.set_password(user.password)
            user.save()

            # 现在处理 UserProfile 实例
            # 因为要自行处理 user 属性，所以设定 commit=False
            # 延迟保存模型，以防出现完整性问题
            profile = profile_form.save(commit=False)
            profile.user = user

            # 用户提供头像了吗？
            # 如果提供了，从表单数据库中提取出来，赋给 UserProfile 模型
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # 保存 UserProfile 模型实例
            profile.save()

            # 更新变量的值，告诉模板成功注册了
            registered = True
        else:
            # 表单数据无效，出错了？
            # 在终端打印问题
            print(user_form.errors, profile_form.errors)
    else:
        # 不是 HTTP POST 请求，渲染两个 ModelForm 实例
        # 表单为空，待用户填写
        user_form = UserForm()
        profile_form = UserProfileForm()

    # 根据上下文渲染模板
    return render(request,
        'rango/register.html', {'user_form': user_form,
                    'profile_form': profile_form,
                    'registered': registered})

def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed
        # to request.POST['<variable>'], because the
        # request.POST.get('<variable>') returns None if the
        # value does not exist, while request.POST['<variable>']
        # will raise a KeyError exception.
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html')

# Use the login_required() decorator to ensure only those logged in can
# access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect(reverse('rango:index'))

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')