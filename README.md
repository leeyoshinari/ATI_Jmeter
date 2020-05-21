# ATI_Jmeter
### 介绍
本项目是一整套使用Jmeter+Ant+Python完成接口自动化测试的解决方案；特别是多系统的测试任务执行，要比网上的教程方便的多。<br>

功能：<br>
1. 使用Jmeter维护接口测试用例；
2. 使用Ant执行测试任务，并生成测试报告；
3. 使用Python完成邮件发送及任务调度；
4. 通过get请求触发任务执行，调度方式灵活；
5. 具有定时功能，可周期性或者定时执行测试任务；
6. 通过监控端口，当服务重启后，可自动执行测试任务；
7. 支持自动从git拉取最新版本；

实现：<br>
1. 使用Ant执行Jmeter脚本，并生成测试报告；
2. 考虑到邮件正文内容可读性，定制化修改测试报告模板；
3. 使用正则表达式提取测试报告中的信息，重新组合成邮件正文；
4. 通过get请求触发测试任务的执行；
5. 通过线程池+队列的方式执行测试任务，可灵活设置线程池大小；
6. 使用aiohttp框架启动后台服务，将测试报告加入到静态资源中，可通过链接访问；
7. 每次执行测试任务前，自动从git拉取最新版本；如git pull时需要登录，需要提前配置免登录；

生成的测试报告：<br>
1. Ant生成的测试报告，[长这个样子](https://github.com/leeyoshinari/ATI_Jmeter/blob/master/report/Baidu_AutoTest_Report20200512012447.html) <br>
2. 邮件收到的测试报告，[长这个样子](https://github.com/leeyoshinari/ATI_Jmeter/blob/master/report/send_Baidu_AutoTest_Report20200512012447.html) <br>

### 部署
1、Jmeter和Ant部署参考网上教程，主要介绍测试报告模板修改和build.xml文件<br>
> 测试报告模板是在jmeter自带模板的基础上修改的，主要修改详见`res`文件夹中的`report`截图，说明如下，其他小的修改这里不赘述，可使用文档比较工具自行比较查看，也可[在线文档比较](http://www.jq22.com/textDifference) ;<br>
>> (1) 截图中标注的修改1和修改5，因为默认模板带有2个png的静态文件，生成测试报告时必须带上这2个静态文件，否则测试报告页面不好看，因此，需要去掉这2个静态文件；<br>
>> (2) 截图中标注的修改2，测试报告一般重点关注测试失败的用例，因此，需要把测试失败的用例展示在前面；<br>
>> (3) 截图中标注的修改3，把标题改成中文，因为测试报告会发给较多的人；如果你在外企工作，可以改成英文，但是相对应的脚本中的正则表达式也需要修改；<br>
>> (4) 截图中标注的修改4，添加了一个空的`span`标签，用于添加自定义的内容，提高发送的测试报告邮件的可读性；<br>
>> (5) 其他未标注出来的修改点，主要是默认模板没有我想看到的数据，把一些没有展示的数据展示出来，把一些“没用的”数据隐藏起来，以及一些样式的修改；<br>

> build.xml文件如下，具体配置已详细说明。强调：为了方便测试报告统一管理，也为了能够自动发送邮件，所有系统的build.xml中的测试报告路径必须是同一个文件夹<br>
    ![build文件](https://github.com/leeyoshinari/ATI_Jmeter/blob/master/res/build.png)

2、克隆repository<br>
    ```git clone https://github.com/leeyoshinari/ATI_Jmeter.git``` <br>

3、测试用例放置<br>
> (1)所有测试用例放在一个统一的文件夹中，例如`testCase`文件夹；<br>
> (2)针对不同系统的不同测试用例，可单独再放入一个文件夹中管理，例如：百度的测试用例放在`baidu`中、百度的BVT测试用例放在`baidu_bvt`中、腾讯的测试用例放在`tencent`中；<br>
> (3)每个系统的测试用例文件夹中，都需要放一个配置好的`build.xml`文件；注意：所有系统的测试报告路径必须是同一个文件夹；<br>
> (4)测试用例文件夹具体结构如下：<br>
> ![文件夹结构](https://github.com/leeyoshinari/ATI_Jmeter/blob/master/res/file_structure.png)

强烈建议文件夹及文件名称使用英文<br>
为什么要按照上面的要求放置测试用例？这样放置方便执行测试任务，通过get请求`http://ip:port/run/baidu`就可以执行百度的测试用例，请求`http://ip:port/run/baidu_bvt`就可以执行百度BVT的测试用例。<br>

4、修改配置文件config.conf<br>
> (1)线程池大小，建议设置1就够了；如确实调度较多测试用例的执行，可酌情增加；<br>
> (2)测试用例路径和测试报告路径，建议使用绝对路径；其中测试报告路径应和`build.xml`文件中的路径保持一致；<br>
> (3)如接口自动化脚本维护在git上，可配置git本地仓库路径，每次执行任务前，自动从git上拉取最新版本，默认拉取主分支；前提是已经clone到本地了；<br>
> (4)邮件发送配置，请确认SMTP服务配置正确；邮箱登录密码配置，请在`sendEmail.py`文件中第48行设置，如果密码不想让其他人看到，请将该py文件进行编译，或者直接将这个repository打包，具体打包方法，请往下看；<br>

5、运行<br>
> Linux:<br>
> ```nohup python3 server.py &``` <br>
> Windows<br>
> ```python server.py``` <br>

6、打包<br>
经过前5步，如果该repository可以启动，且执行测试任务成功，则可以进行打包，使用pyinstaller进行打包。<br>
pyinstaller安装自行查找教程，须确保安装正确，否则打包会报错，下面直接进行打包：
> (1)进入ATI_Jmeter文件夹，执行命令：<br>
> ```shell
> pyinstaller server.py -p schedule.py -p logger.py -p config.py -p sendEmail.py -p testing.py --hidden-import logger --hidden-import schedule --hidden-import config --hidden-import sendEmail --hidden-import testing
> ```
> (2)打包完成后，在当前路径下会生成dist文件夹，进入dist/server即可找到可执行文件server；<br>
> (3)将配置文件config.conf拷贝到dist/server文件夹下，并修改配置文件；<br>
> (4)如需要部署在其他服务器上，可将dist/server整个文件夹拷贝到其他服务器，启动server <br>
> ```nohup ./server &```

7、CI/CD，以Jenkins为例，在Jenkins构建后操作中增加一个get请求，请求的url为`http://IP:PORT/run/系统名称`，此处系统名称应和testCase用例文件夹中的对应的系统名称保持一致。

8、如果你所在的项目还没有用到CI/CD，或者项目本身有较多配置项，每次手动更改配置重启项目后，也想自动执行测试任务；亦或是你不想配置CI/CD，则需要执行客户端；<br>
进入client文件夹，将脚本和配置文件拷贝到项目所在的服务器上，运行即可，也可以按照步骤6的方式进行打包。<br>

修改配置文件config.conf：<br>
> (1)系统名称必须和测试用例文件夹中的名称保持一致，例如可配置成`baidu`；如需测试多个系统，名字用英文逗号`,`隔开；<br>
> (2)系统端口号即系统占用的端口号；如需监控多个系统的端口，端口用英文逗号`,`隔开；<br>
注意：如测试多个系统，系统名称的排序和系统端口的排序必须保持一致

### 注意
1、如需部署client，部署的服务器必须支持`netstat`命令，以便根据端口号查进程号；仅支持Linux系统；<br>
2、已经测试的版本：Jmeter-5.2.1、Ant-1.10.7<br>
3、另外还有一个项目，使用Python编写的接口自动化测试框架，用Excel维护测试用例，感兴趣的话[可以点我](https://github.com/leeyoshinari/ATI) 。

### Requirements
1. aiohttp>=3.6.2
2. GitPython>=3.1.2
3. requests
4. Python 3.7+
