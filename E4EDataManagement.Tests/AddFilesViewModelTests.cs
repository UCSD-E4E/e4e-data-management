using E4EDataManagement.UI.ViewModels;
using Xunit;

namespace E4EDataManagement.Tests;

public class AddFilesViewModelTests
{
    [Fact]
    public void InitialState_NoFiles_CanConfirmIsFalse()
    {
        var vm = new AddFilesViewModel();
        Assert.Empty(vm.Files);
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void InitialState_CanRemoveIsFalse()
    {
        var vm = new AddFilesViewModel();
        Assert.False(vm.CanRemove);
    }

    [Fact]
    public void AddFile_AddsToCollection_CanConfirmBecomesTrue()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/path/to/file.bin");
        Assert.Single(vm.Files);
        Assert.True(vm.CanConfirm);
    }

    [Fact]
    public void AddFile_DuplicatePath_NotAddedTwice()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/path/to/file.bin");
        vm.AddFile("/path/to/file.bin");
        Assert.Single(vm.Files);
    }

    [Fact]
    public void AddFile_MultipleDistinct_AllAdded()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/a.bin");
        vm.AddFile("/b.bin");
        Assert.Equal(2, vm.Files.Count);
    }

    [Fact]
    public void SelectedFile_WhenSet_CanRemoveIsTrue()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/a.bin");
        vm.SelectedFile = "/a.bin";
        Assert.True(vm.CanRemove);
    }

    [Fact]
    public void RemoveSelectedCommand_RemovesFile_CanConfirmFalseWhenEmpty()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/a.bin");
        vm.SelectedFile = "/a.bin";
        vm.RemoveSelectedCommand.Execute(null);
        Assert.Empty(vm.Files);
        Assert.False(vm.CanConfirm);
    }

    [Fact]
    public void RemoveSelectedCommand_LeavesOtherFiles()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/a.bin");
        vm.AddFile("/b.bin");
        vm.SelectedFile = "/a.bin";
        vm.RemoveSelectedCommand.Execute(null);
        Assert.Single(vm.Files);
        Assert.Equal("/b.bin", vm.Files[0]);
    }

    [Fact]
    public void RemoveSelectedCommand_WhenNothingSelected_DoesNotThrow()
    {
        var vm = new AddFilesViewModel();
        vm.AddFile("/a.bin");
        vm.SelectedFile = null;
        var ex = Record.Exception(() => vm.RemoveSelectedCommand.Execute(null));
        Assert.Null(ex);
        Assert.Single(vm.Files);
    }
}
